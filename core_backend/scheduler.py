import os
import logging
import httpx
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from .database import engine, SessionLocal
from . import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AI_Pricing_Scheduler")

# Store the last action's state for each product so we can compute reward
# Key: product_id -> { state, action, old_price }
_last_actions = {}

def background_pricing_job():
    logger.info(f"[{datetime.utcnow()}] Running AI automated pricing optimization cycle...")
    db: Session = SessionLocal()
    try:
        # We can't query Product.inventory directly anymore since it's an @property
        # Instead we'll query all active products and filter out zero-inventory in Python
        all_products = db.query(models.Product).filter(models.Product.is_active == True).all()
        products = [p for p in all_products if p.inventory > 0][:250]
        
        for p in products:
            # 1. Fetch traffic and sales data across all product variants
            traffic_count = db.query(models.TrafficLog).filter(models.TrafficLog.product_id == p.id).count()
            
            recent_items = db.query(models.OrderItem)\
                .join(models.ProductVariant, models.OrderItem.variant_id == models.ProductVariant.id)\
                .filter(models.ProductVariant.product_id == p.id).all()
                
            total_sales = sum(item.quantity for item in recent_items)
            total_revenue = sum(item.quantity * item.price_at_purchase for item in recent_items)

            # 2. REWARD FEEDBACK: If we have a previous action for this product, send the reward
            if p.id in _last_actions:
                prev = _last_actions[p.id]
                # Reward = revenue earned from this product since last cycle
                # Simple: (new_sales * current_price) - (new_sales * cost_price)
                cost_price = float(p.cost_price) if p.cost_price else float(p.base_price) * 0.4
                new_sales_since = total_sales - prev.get("prev_total_sales", 0)
                
                if new_sales_since > 0:
                    reward = (new_sales_since * float(p.current_price)) - (new_sales_since * cost_price)
                else:
                    # Small negative reward for no sales (opportunity cost)
                    reward = -0.5

                # Build the new state vector
                predicted_demand = prev.get("predicted_demand", 0.0)
                next_state = [
                    float(p.current_price) / 500.0,
                    float(p.base_price) / 500.0,
                    p.inventory / 500.0,
                    traffic_count / 100.0,
                    total_sales / 50.0,
                    predicted_demand / 100.0,
                    abs(predicted_demand * 0.12) / 100.0,  # uncertainty estimate
                    datetime.utcnow().weekday() / 6.0,     # day_of_week
                    1.0 if float(p.current_price) < float(p.base_price) * 0.85 else 0.0,  # promotion
                    0.0,  # price_volatility placeholder
                ]

                # Send reward to the SAC agent
                try:
                    reward_payload = {
                        "product_id": p.id,
                        "state": prev["state"],
                        "action": prev["action"],
                        "reward": reward,
                        "next_state": next_state,
                        "done": False,
                    }
                    ai_url = os.environ.get("AI_SERVICE_URL", "http://ai_engine:8001")
                    httpx.post(f"{ai_url}/reward", json=reward_payload, timeout=3.0)
                except Exception as e:
                    logger.warning(f"Failed to send reward for product {p.id}: {e}")

            # 3. Call the AI microservice for a NEW pricing action
            try:
                ai_request = {
                    "product_id": p.id,
                    "current_price": float(p.current_price),
                    "base_price": float(p.base_price),
                    "cost_price": float(p.cost_price) if p.cost_price else 0.0,
                    "inventory": p.inventory,
                    "traffic": traffic_count,
                    "sales": total_sales,
                }
                
                ai_url = os.environ.get("AI_SERVICE_URL", "http://ai_engine:8001")
                response = httpx.post(f"{ai_url}/optimize-price", json=ai_request, timeout=3.0)
                
                if response.status_code == 200:
                    ai_data = response.json()
                    new_price = ai_data.get("optimized_price")
                    predicted_demand = ai_data.get("predicted_demand", 0.0)
                    price_multiplier = ai_data.get("price_multiplier", 1.0)
                    state_vector = ai_data.get("state", [])
                    model_version = ai_data.get("model_version", "unknown")

                    if new_price and abs(new_price - float(p.current_price)) > 0.01:
                        old_price = float(p.current_price)
                        p.current_price = round(new_price, 2)
                        
                        # Log the AI decision to PriceHistory
                        history = models.PriceHistory(
                            product_id=p.id,
                            old_price=old_price,
                            new_price=p.current_price,
                            reason=f"SAC RL Agent. Traffic: {traffic_count}, Sales: {total_sales}, Multiplier: {price_multiplier:.3f}",
                            demand_score=predicted_demand
                        )
                        db.add(history)
                        logger.info(f"[SAC RL] {p.name}: ${old_price:.2f} -> ${p.current_price:.2f} (x{price_multiplier:.3f}) [{model_version}]")

                    # Store the action for reward computation next cycle
                    _last_actions[p.id] = {
                        "state": state_vector,
                        "action": price_multiplier,
                        "prev_total_sales": total_sales,
                        "predicted_demand": predicted_demand,
                    }

            except Exception as e:
                logger.warning(f"Failed to communicate with AI Service for product {p.id}: {e}")

        db.commit()
    except Exception as e:
        logger.error(f"Error in background_pricing_job: {e}")
    finally:
        db.close()

# Scheduler instance
scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(background_pricing_job, 'interval', days=3, id='ai_pricing_optimizer_job', replace_existing=True)
    scheduler.start()
    logger.info("SAC RL Pricing Scheduler started. Agent will learn from live user data every 3 days.")

def shutdown_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler shutdown.")
