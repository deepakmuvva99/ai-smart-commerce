from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import random
import torch
import numpy as np
import datetime
import os
import logging
import pickle

from ai_service.models.demand_model import (
    DemandForecastingModel, load_demand_model, FEATURES, N_FEAT, SEQ_LEN
)
from ai_service.models.sac_agent import SACAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AI_Service")

# ============================================================
# Request / Response Models
# ============================================================

class PriceOptimizationRequest(BaseModel):
    product_id: int
    current_price: float
    base_price: float = 0.0
    cost_price: float = 0.0
    inventory: int = 0
    traffic: int = 0
    sales: int = 0

class RewardFeedbackRequest(BaseModel):
    product_id: int
    state: list          # The state vector used when the action was taken
    action: float        # The price multiplier that was applied
    reward: float        # Revenue earned since last cycle
    next_state: list     # The new state vector after the action
    done: bool = False

app = FastAPI(title="Smart Commerce AI Microservice")

# ============================================================
# Load Models at Startup
# ============================================================

# 1. LSTM Demand Forecasting Model (V5 -- BiLSTM + Attention)
MODEL_LOADED = False
product_scalers = {}
try:
    model_path = os.path.join(os.path.dirname(__file__), 'exports', 'demand_model.pt')
    demand_model = load_demand_model(model_path, device='cpu')
    MODEL_LOADED = True
    logger.info("Loaded V5 BiLSTM Demand Forecasting Model.")

    scaler_path = os.path.join(os.path.dirname(__file__), 'exports', 'product_scalers.pkl')
    if os.path.exists(scaler_path):
        with open(scaler_path, 'rb') as f:
            product_scalers = pickle.load(f)
        logger.info(f"Loaded {len(product_scalers)} product scalers.")
    else:
        logger.warning("product_scalers.pkl not found. Demand predictions will use fallback.")
except Exception as e:
    logger.warning(f"Could not load demand model: {e}")

# 2. SAC Reinforcement Learning Agent (V5)
sac_agent = SACAgent(state_dim=10, action_dim=1, hidden_dim=256)
sac_dir = os.path.join(os.path.dirname(__file__), 'exports', 'sac_checkpoint')
if sac_agent.load(sac_dir):
    logger.info(f"Loaded existing SAC agent checkpoint. Total updates: {sac_agent.total_updates}")
else:
    logger.info("No SAC checkpoint found. Starting fresh RL agent — it will learn from live data.")


# ============================================================
# Endpoints
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai_engine",
        "lstm_model_loaded": MODEL_LOADED,
        "sac_agent_updates": sac_agent.total_updates,
        "sac_buffer_size": len(sac_agent.replay_buffer),
    }


def _build_feature_sequence(current_price, base_price, traffic, sales, inventory, day_of_week):
    """Build a synthetic 14-day feature sequence for inference when no scaler is available."""
    log_units = np.log1p(max(0, sales))
    promotion = 1.0 if current_price < base_price * 0.85 else 0.0
    row = [
        log_units,          # log_units_sold
        current_price,      # current_price
        traffic,            # num_invoices (traffic proxy)
        1.0,                # basket_size (default)
        promotion,          # promotion_flag
        0.0,                # price_volatility_7d
        1.0,                # days_since_last
        day_of_week,        # day_of_week
        inventory,          # inventory_level
    ]
    return [row for _ in range(SEQ_LEN)]


def _mc_dropout_predict(model, x_tensor, n_passes=10):
    """Monte Carlo Dropout for uncertainty estimation."""
    model.train()  # enable dropout
    preds = []
    with torch.no_grad():
        for _ in range(n_passes):
            preds.append(model(x_tensor).item())
    model.eval()
    return float(np.mean(preds)), float(np.std(preds))


@app.get("/predict-demand")
def predict_demand(product_id: int, current_price: float = 100.0,
                   base_price: float = 0.0, traffic: int = 0,
                   sales: int = 0, inventory: int = 100):
    """Use the V5 BiLSTM model to predict demand for a product."""
    if not MODEL_LOADED:
        return {"product_id": product_id, "predicted_demand": 0.0,
                "uncertainty": 0.0, "error": "Model not loaded"}

    try:
        bp = base_price if base_price > 0 else current_price
        day_of_week = datetime.datetime.today().weekday()
        seq = _build_feature_sequence(current_price, bp, traffic, sales, inventory, day_of_week)
        x_np = np.array([seq], dtype=np.float32)

        # Use per-product scaler if available
        scaler = product_scalers.get(product_id)
        if scaler:
            x_np[0] = scaler.transform(x_np[0])

        x_tensor = torch.from_numpy(x_np)

        # MC-Dropout for mean + uncertainty
        pred_norm_mean, pred_norm_std = _mc_dropout_predict(demand_model, x_tensor)

        # Inverse transform: Z-score -> log1p -> real units
        if scaler:
            dummy = np.zeros((1, N_FEAT))
            dummy[0, 0] = pred_norm_mean
            log_pred = scaler.inverse_transform(dummy)[0, 0]
            predicted_demand = float(np.expm1(log_pred))
            # Approximate uncertainty in real units
            dummy[0, 0] = pred_norm_std
            log_unc = abs(scaler.inverse_transform(dummy)[0, 0])
            uncertainty = float(np.expm1(abs(log_unc)))
        else:
            predicted_demand = float(np.expm1(abs(pred_norm_mean)))
            uncertainty = float(np.expm1(abs(pred_norm_std)))

        return {
            "product_id": product_id,
            "predicted_demand": round(max(0, predicted_demand), 2),
            "uncertainty": round(max(0, uncertainty), 2),
        }
    except Exception as e:
        return {"product_id": product_id, "predicted_demand": 0.0,
                "uncertainty": 0.0, "error": str(e)}


@app.post("/optimize-price")
def optimize_price(req: PriceOptimizationRequest):
    """
    Use the SAC RL Agent to determine the optimal price multiplier.
    
    The agent observes the state and outputs a learned pricing action.
    If insufficient training data exists, it explores aggressively.
    """
    # Step 1: Get demand prediction from V5 BiLSTM
    predicted_demand = 0.0
    if MODEL_LOADED:
        try:
            bp = req.base_price if req.base_price > 0 else req.current_price
            day_of_week = datetime.datetime.today().weekday()
            seq = _build_feature_sequence(
                req.current_price, bp, req.traffic, req.sales, req.inventory, day_of_week)
            x_np = np.array([seq], dtype=np.float32)

            scaler = product_scalers.get(req.product_id)
            if scaler:
                x_np[0] = scaler.transform(x_np[0])

            x_tensor = torch.from_numpy(x_np)
            with torch.no_grad():
                pred_norm = demand_model(x_tensor).item()

            if scaler:
                dummy = np.zeros((1, N_FEAT))
                dummy[0, 0] = pred_norm
                log_pred = scaler.inverse_transform(dummy)[0, 0]
                predicted_demand = float(np.expm1(log_pred))
            else:
                predicted_demand = float(np.expm1(abs(pred_norm)))

            predicted_demand = max(0, predicted_demand)
        except Exception as e:
            logger.warning(f"LSTM inference failed: {e}")

    # Step 2: Build 10-dim state vector for V5 RL agent
    base_price = req.base_price if req.base_price > 0 else req.current_price
    cost_price = req.cost_price if req.cost_price > 0 else req.current_price * 0.4
    day_of_week = datetime.datetime.today().weekday()
    promotion_flag = 1.0 if req.current_price < base_price * 0.85 else 0.0

    state = [
        req.current_price / 500.0,       # Normalize price
        base_price / 500.0,
        req.inventory / 500.0,           # Normalize inventory
        req.traffic / 100.0,             # Normalize traffic
        req.sales / 50.0,                # Normalize sales
        predicted_demand / 100.0,        # Normalize demand prediction
        abs(predicted_demand * 0.12) / 100.0,  # Estimated uncertainty
        day_of_week / 6.0,              # Day of week normalized
        promotion_flag,                  # Is on promotion
        0.0,                             # Price volatility (will be filled by scheduler)
    ]

    # Step 3: Ask the SAC agent for a pricing action
    # Use evaluation mode if agent has enough training data
    evaluate = sac_agent.total_updates > 100
    price_multiplier = sac_agent.select_action(state, evaluate=evaluate)

    # Step 4: Calculate the new price
    new_price = base_price * price_multiplier

    # Safety bounds: never below cost, never above 3x base
    new_price = max(cost_price * 1.05, min(new_price, base_price * 3.0))

    model_version = f"bilstm-v5 + sac-rl (updates: {sac_agent.total_updates}, buffer: {len(sac_agent.replay_buffer)})"

    return {
        "product_id": req.product_id,
        "optimized_price": round(new_price, 2),
        "price_multiplier": round(price_multiplier, 4),
        "predicted_demand": round(predicted_demand, 2),
        "model_version": model_version,
        "state": state,  # Return state so scheduler can feed it back as reward later
    }


@app.post("/reward")
def receive_reward(feedback: RewardFeedbackRequest, background_tasks: BackgroundTasks):
    """
    Receive reward feedback from the scheduler after a pricing cycle.
    The heavy RL model update is shunted to a Background Task to prevent blocking the API.
    """
    def process_rl_update():
        sac_agent.store_transition(
            state=feedback.state,
            action=feedback.action,
            reward=feedback.reward,
            next_state=feedback.next_state,
            done=feedback.done,
        )

        if len(sac_agent.replay_buffer) >= 32:
            sac_agent.update(batch_size=64)
            if sac_agent.total_updates % 50 == 0:
                sac_agent.save(sac_dir)
                logger.info(f"SAC checkpoint saved at update {sac_agent.total_updates}")

    background_tasks.add_task(process_rl_update)

    return {
        "status": "reward_training_queued",
        "message": "RL update deferred to background processor"
    }


@app.post("/retrain")
def trigger_retraining(background_tasks: BackgroundTasks):
    """Force a batch of SAC training updates."""
    def batch_train():
        for _ in range(100):
            sac_agent.update(batch_size=64)
        sac_agent.save(sac_dir)
        logger.info(f"Batch retraining complete. Total updates: {sac_agent.total_updates}")

    background_tasks.add_task(batch_train)
    return {"message": "Batch SAC retraining started in background", "current_updates": sac_agent.total_updates}
