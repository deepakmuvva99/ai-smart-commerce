"""
Train the SAC Pricing Agent (V5) using the V5 BiLSTM demand model
and real elasticity estimated from the Online Retail II dataset.
Saves weights to exports/sac_checkpoint/.
"""

import os, sys, random, pickle
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models.sac_agent import SACAgent
from models.demand_model import DemandForecastingModel, load_demand_model, FEATURES, N_FEAT, SEQ_LEN

SEED = 42
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
DEVICE = torch.device("cpu")

# ── Load demand model & scalers ──────────────────────────────────────────
print("Loading V5 demand model and scalers...")
lstm_model = load_demand_model("exports/demand_model.pt", device="cpu")

scaler_path = "exports/product_scalers.pkl"
with open(scaler_path, "rb") as f:
    product_scalers = pickle.load(f)
print(f"  Loaded {len(product_scalers)} product scalers")

# ── Load & clean data (same pipeline as train_v5.py) ─────────────────────
print("Loading Online Retail II dataset...")
DATA_PATH = "dataset/online_retail_II.csv"
raw = pd.read_csv(DATA_PATH, encoding="utf-8", low_memory=False)
raw.columns = raw.columns.str.strip()

df = raw.copy()
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], dayfirst=True, errors="coerce")
df = df.dropna(subset=["InvoiceDate"])
df = df[~df["Invoice"].astype(str).str.startswith("C")]
df = df[(df["Quantity"] > 0) & (df["Price"] > 0)]
df = df.dropna(subset=["StockCode", "Description"])
df["StockCode"] = df["StockCode"].astype(str).str.strip()
df = df[df["StockCode"].str.match(r"^\d{5}[A-Z]?$", na=False)]
df = df[df["Country"] == "United Kingdom"].copy()
df["date"] = df["InvoiceDate"].dt.normalize()
df["day_of_week"] = df["InvoiceDate"].dt.dayofweek

daily = (
    df.groupby(["StockCode", "date"])
      .agg(units_sold=("Quantity", "sum"),
           current_price=("Price", "median"),
           num_invoices=("Invoice", "nunique"),
           day_of_week=("day_of_week", "first"))
      .reset_index()
)
basket = (
    df.groupby(["Invoice", "date"])["StockCode"]
      .nunique().reset_index(name="basket_size")
      .groupby("date")["basket_size"].mean().reset_index()
)
daily = daily.merge(basket, on="date", how="left")
daily["basket_size"] = daily["basket_size"].fillna(1.0).clip(lower=1.0)

MIN_RECORDS = 200

def engineer(pdf):
    pdf = pdf.sort_values("date").reset_index(drop=True)
    cutoff = pdf["date"].iloc[0] + pd.Timedelta(days=90)
    warm = pdf.loc[pdf["date"] <= cutoff, "current_price"]
    bp = float(warm.median()) if len(warm) >= 3 else float(pdf["current_price"].median())
    pdf["base_price"] = bp
    pdf["promotion_flag"] = (pdf["current_price"] < bp * 0.85).astype(float)
    pdf["price_volatility_7d"] = pdf["current_price"].rolling(7, min_periods=2).std().fillna(0.0)
    pdf["days_since_last"] = pdf["date"].diff().dt.days.fillna(1.0).clip(upper=30.0)
    pdf["log_units_sold"] = np.log1p(pdf["units_sold"])
    inv, inv_list = 500, []
    for q in pdf["units_sold"].astype(int):
        inv = max(0, inv - q)
        if inv < 50: inv += 400
        inv_list.append(inv)
    pdf["inventory_level"] = inv_list
    return pdf

frames = []
for sc, grp in daily.groupby("StockCode"):
    if len(grp) >= MIN_RECORDS:
        frames.append(engineer(grp))

df_clean = pd.concat(frames, ignore_index=True)
q99 = df_clean["units_sold"].quantile(0.99)
df_clean["units_sold"] = df_clean["units_sold"].clip(upper=q99)
df_clean["log_units_sold"] = np.log1p(df_clean["units_sold"])
df_clean.sort_values(["StockCode", "date"], inplace=True)
df_clean.reset_index(drop=True, inplace=True)

print(f"  Products: {df_clean['StockCode'].nunique()}, Records: {len(df_clean):,}")


# ── Estimate per-product price elasticity ─────────────────────────────────
def estimate_elasticity(grp):
    g = grp[["units_sold", "current_price"]].dropna()
    g = g[(g["units_sold"] > 0) & (g["current_price"] > 0)]
    if len(g) < 10:
        return -1.2
    lnP = np.log(g["current_price"])
    lnQ = np.log(g["units_sold"])
    if lnP.std() < 1e-6:
        return -1.2
    beta = np.cov(lnP, lnQ)[0, 1] / (np.var(lnP) + 1e-10)
    return float(np.clip(beta, -3.0, -0.1))

elasticities = df_clean.groupby("StockCode").apply(estimate_elasticity).to_dict()
print(f"  Elasticity range: [{min(elasticities.values()):.2f}, {max(elasticities.values()):.2f}]")


# ── Normalisation constants ───────────────────────────────────────────────
_pmax = df_clean["current_price"].quantile(0.99) + 1e-6
_imax = df_clean["inventory_level"].max() + 1
_tmax = df_clean["num_invoices"].quantile(0.99) + 1e-6
_umax = df_clean["units_sold"].quantile(0.99) + 1e-6
_vmax = df_clean["price_volatility_7d"].quantile(0.99) + 1e-6


def build_state(row, pred_d, pred_unc):
    return [
        min(row["current_price"]       / _pmax, 3.0),
        min(row["base_price"]          / _pmax, 3.0),
        min(row["inventory_level"]     / _imax, 3.0),
        min(row["num_invoices"]        / _tmax, 3.0),
        min(row["units_sold"]          / _umax, 3.0),
        min(abs(pred_d)                / _umax, 3.0),
        min(abs(pred_unc)              / _umax, 3.0),
        row["day_of_week"]             / 6.0,
        float(row["promotion_flag"]),
        min(row["price_volatility_7d"] / _vmax, 3.0),
    ]


def compute_reward(sales, price, base_price, mult, inventory, pred_demand=None):
    revenue = float(sales) * price
    margin  = max(0.0, price - base_price * 0.60) * 0.5
    vol_pen = 80.0 * (mult - 1.0) ** 2
    cliff   = 300.0 if (mult > 1.20 and inventory < 30) else 0.0
    stk_pen = 150.0 if sales >= inventory else 0.0
    dem_bon = 0.0
    if pred_demand and pred_demand > 0:
        align = max(0.0, 1.0 - abs(sales - pred_demand) / (pred_demand + 1e-6))
        dem_bon = align * base_price * 0.12
    return revenue + margin + dem_bon - vol_pen - cliff - stk_pen


# ── MC-Dropout demand prediction helper ──────────────────────────────────
def mc_uncertainty(model, x, n=5):
    model.train()
    with torch.no_grad():
        s = torch.stack([model(x) for _ in range(n)])
    model.eval()
    return s.mean(0).cpu().numpy(), s.std(0).cpu().numpy()


# ── SAC TRAINING ──────────────────────────────────────────────────────────
print("\n" + "=" * 68)
print("  TRAINING SAC PRICING AGENT (V5)")
print("=" * 68)

EPISODES = 3000
STEPS    = 25
WARMUP   = 1000

sac_agent = SACAgent(state_dim=10, action_dim=1, hidden_dim=256)
pool = df_clean.reset_index(drop=True)
rew_hist = []
total_steps = 0

for ep in range(1, EPISODES + 1):
    ep_rew = 0.0
    for _ in range(STEPS):
        idx = random.randint(0, len(pool) - 1)
        row = pool.iloc[idx]
        sc  = row["StockCode"]
        bp  = row["base_price"]
        elas = elasticities.get(sc, -1.2)

        # Try to get LSTM demand prediction
        sc_data = df_clean[df_clean["StockCode"] == sc].sort_values("date")
        loc = sc_data.index.get_loc(row.name) if row.name in sc_data.index else -1
        if loc >= SEQ_LEN and sc in product_scalers:
            ctx = sc_data.iloc[loc - SEQ_LEN:loc][FEATURES]
            sclr = product_scalers[sc]
            ct = torch.from_numpy(sclr.transform(ctx)[np.newaxis].astype(np.float32)).to(DEVICE)
            pm, ps = mc_uncertainty(lstm_model, ct, n=5)
            pred_d = float(np.expm1(abs(
                sclr.inverse_transform(
                    np.array([[pm.ravel()[0]] + [0] * (N_FEAT - 1)]))[0, 0])))
            pred_unc = float(abs(pred_d * 0.12))
        else:
            pred_d = float(row["units_sold"]) * random.uniform(0.85, 1.15)
            pred_unc = abs(pred_d) * 0.12

        state = build_state(row, pred_d, pred_unc)

        if total_steps < WARMUP:
            mult = random.uniform(0.70, 1.30)
        else:
            mult = sac_agent.select_action(state, evaluate=False)

        new_p = float(np.clip(row["current_price"] * mult, bp * 0.70, bp * 1.30))
        pct_pc = (new_p - row["current_price"]) / (row["current_price"] + 1e-6)
        sales = max(0, int(row["units_sold"] * (1.0 + elas * pct_pc)))
        rew = compute_reward(sales, new_p, bp, mult, int(row["inventory_level"]), pred_d)

        next_state = state  # simplified: same state for terminal
        sac_agent.store_transition(state, mult, rew, next_state, done=False)

        if total_steps >= WARMUP:
            sac_agent.update(batch_size=256)

        ep_rew += rew
        total_steps += 1

    rew_hist.append(ep_rew)
    if ep % 500 == 0:
        print(f"  Ep {ep:4d}/{EPISODES}  "
              f"AvgRew={np.mean(rew_hist[-500:]):>12,.0f}  "
              f"alpha={sac_agent.alpha:.4f}  buf={len(sac_agent.replay_buffer):,}")

# ── Save ──────────────────────────────────────────────────────────────────
print("\nSaving SAC agent...")
sac_dir = "exports/sac_checkpoint"
sac_agent.save(sac_dir)
print(f"  SAC agent saved to {sac_dir}/")
print(f"  Total updates: {sac_agent.total_updates}")

# Also save to v5_results for reference
sac_agent.save("v5_results/sac_checkpoint")

print("\n" + "=" * 68)
print("  SAC TRAINING COMPLETE")
print("=" * 68)
