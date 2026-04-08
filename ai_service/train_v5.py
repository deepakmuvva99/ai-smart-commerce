"""
================================================================================
  V5 Training Pipeline  --  UCI Online Retail II Dataset
  BiLSTM-Attention Demand Forecaster (Pooled Multi-Product)
================================================================================
Adapted from the Colab v5 notebook to run locally.
Reads: dataset/online_retail_II.csv
Outputs: v5_results/  (model weights, scalers, figures, metrics)
================================================================================
"""

import os, random, warnings, pickle, copy
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # non-interactive backend for local
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from scipy import stats

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from models.demand_model_v5 import DemandForecastingModel, FEATURES, N_FEAT, SEQ_LEN

warnings.filterwarnings("ignore")

SEED = 42
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {DEVICE}")

RESULTS_DIR = "v5_results"
os.makedirs(RESULTS_DIR, exist_ok=True)
DATA_PATH = "dataset/online_retail_II.csv"

MIN_RECORDS = 200  # minimum daily records per product


# =============================================================================
#  BLOCK A  DATA CLEANING & FEATURE ENGINEERING
# =============================================================================
print("=" * 68)
print("  BLOCK A -- DATA CLEANING & FEATURE ENGINEERING")
print("=" * 68)

# A-1  Load
print("\n[A-1] Loading ...")
raw = None
for enc in ("utf-8", "latin-1", "cp1252"):
    try:
        raw = pd.read_csv(DATA_PATH, encoding=enc, low_memory=False)
        print(f"  Encoding={enc}  shape={raw.shape}")
        break
    except Exception:
        continue
if raw is None:
    raise RuntimeError(f"Cannot load {DATA_PATH}")
raw.columns = raw.columns.str.strip()

# A-2  Clean
print("\n[A-2] Cleaning ...")
df = raw.copy()
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], dayfirst=True, errors="coerce")
df = df.dropna(subset=["InvoiceDate"])

n0 = len(df)
df = df[~df["Invoice"].astype(str).str.startswith("C")]
df = df[(df["Quantity"] > 0) & (df["Price"] > 0)]
print(f"  Removed cancellations / returns   : -{n0-len(df):,}  left: {len(df):,}")

df = df.dropna(subset=["StockCode","Description"])
df["StockCode"] = df["StockCode"].astype(str).str.strip()
n1 = len(df)
df = df[df["StockCode"].str.match(r"^\d{5}[A-Z]?$", na=False)]
print(f"  Non-product StockCodes removed    : -{n1-len(df):,}  left: {len(df):,}")

n2 = len(df)
df = df[df["Country"] == "United Kingdom"].copy()
print(f"  Non-UK rows removed               : -{n2-len(df):,}  left: {len(df):,}")

df["date"]        = df["InvoiceDate"].dt.normalize()
df["day_of_week"] = df["InvoiceDate"].dt.dayofweek
print(f"  Date range : {df['date'].min().date()} -> {df['date'].max().date()}")
print(f"  Unique products : {df['StockCode'].nunique():,}")

# A-3  Daily aggregation
print("\n[A-3] Daily aggregation ...")
daily = (
    df.groupby(["StockCode","date"])
      .agg(units_sold    = ("Quantity",    "sum"),
           current_price = ("Price",       "median"),
           num_invoices  = ("Invoice",     "nunique"),
           day_of_week   = ("day_of_week", "first"))
      .reset_index()
)
basket = (
    df.groupby(["Invoice","date"])["StockCode"]
      .nunique()
      .reset_index(name="basket_size")
      .groupby("date")["basket_size"].mean()
      .reset_index()
)
daily = daily.merge(basket, on="date", how="left")
daily["basket_size"] = daily["basket_size"].fillna(1.0).clip(lower=1.0)
print(f"  Daily records: {len(daily):,}  Products: {daily['StockCode'].nunique():,}")

# A-4  Per-product features
print("\n[A-4] Feature engineering per product ...")

def engineer(pdf):
    pdf = pdf.sort_values("date").reset_index(drop=True)
    cutoff = pdf["date"].iloc[0] + pd.Timedelta(days=90)
    warm   = pdf.loc[pdf["date"] <= cutoff, "current_price"]
    bp     = float(warm.median()) if len(warm) >= 3 else float(pdf["current_price"].median())
    pdf["base_price"]          = bp
    pdf["promotion_flag"]      = (pdf["current_price"] < bp * 0.85).astype(float)
    pdf["price_volatility_7d"] = (pdf["current_price"]
                                    .rolling(7, min_periods=2).std().fillna(0.0))
    pdf["days_since_last"]     = (pdf["date"].diff().dt.days.fillna(1.0).clip(upper=30.0))
    pdf["log_units_sold"]      = np.log1p(pdf["units_sold"])

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
df_clean.sort_values(["StockCode","date"], inplace=True)
df_clean.reset_index(drop=True, inplace=True)

# Clip extreme outliers in units_sold (top 1%)
q99 = df_clean["units_sold"].quantile(0.99)
df_clean["units_sold"]     = df_clean["units_sold"].clip(upper=q99)
df_clean["log_units_sold"] = np.log1p(df_clean["units_sold"])

n_products = df_clean["StockCode"].nunique()
print(f"  Products >= {MIN_RECORDS} records : {n_products}")
print(f"  Total daily records          : {len(df_clean):,}")
print(f"  Median records per product   : {df_clean.groupby('StockCode').size().median():.0f}")


# =============================================================================
#  BLOCK B  LSTM -- MULTI-PRODUCT POOLED TRAINING
# =============================================================================
print("\n" + "=" * 68)
print("  BLOCK B -- LSTM (Pooled Multi-Product Training)")
print("=" * 68)

def make_sequences(data, seq):
    X, y = [], []
    for i in range(len(data) - seq):
        X.append(data[i: i+seq])
        y.append(data[i+seq, 0])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

# B-1  Per-product Z-score normalisation + pooled sequence building
print("\n[B-1] Building pooled dataset (per-product Z-score) ...")

all_X_tr, all_y_tr = [], []
all_X_te, all_y_te = [], []
product_scalers    = {}
product_test_info  = {}

for sc in df_clean["StockCode"].unique():
    pdf = df_clean[df_clean["StockCode"] == sc].sort_values("date").reset_index(drop=True)
    if len(pdf) < SEQ_LEN + 20:
        continue

    sp   = int(len(pdf) * 0.80)
    sclr = StandardScaler()
    sclr.fit(pdf.iloc[:sp][FEATURES])
    scaled = sclr.transform(pdf[FEATURES])

    X, y = make_sequences(scaled, SEQ_LEN)
    sp_s  = int(len(X) * 0.80)
    if sp_s < 5 or len(X) - sp_s < 5:
        continue

    all_X_tr.append(X[:sp_s]); all_y_tr.append(y[:sp_s])
    all_X_te.append(X[sp_s:]); all_y_te.append(y[sp_s:])
    product_scalers[sc]   = sclr
    product_test_info[sc] = (X[sp_s:], y[sp_s:], sclr)

X_tr = torch.from_numpy(np.concatenate(all_X_tr)).to(DEVICE)
X_te = torch.from_numpy(np.concatenate(all_X_te)).to(DEVICE)
y_tr = torch.from_numpy(np.concatenate(all_y_tr)).unsqueeze(1).to(DEVICE)
y_te = torch.from_numpy(np.concatenate(all_y_te)).unsqueeze(1).to(DEVICE)

n_train_prod = len(product_scalers)
print(f"  Products in pooled set   : {n_train_prod}")
print(f"  Pooled train sequences   : {X_tr.shape[0]:,}")
print(f"  Pooled test  sequences   : {X_te.shape[0]:,}")
print(f"  Features                 : {N_FEAT}  SEQ_LEN={SEQ_LEN}")

n_params = sum(p.numel() for p in DemandForecastingModel().parameters() if p.requires_grad)
print(f"\n  Model params : {n_params:,}  "
      f"(ratio to train sequences: 1:{X_tr.shape[0]//max(n_params,1)})")


# B-2  Training
def train_model(model, X_tr, y_tr, X_te, y_te,
                epochs=300, batch=512, lr=5e-4, wd=1e-4,
                patience=50, min_epochs=30, label=""):
    loader_tr = DataLoader(TensorDataset(X_tr, y_tr), batch_size=batch, shuffle=True)
    loader_te = DataLoader(TensorDataset(X_te, y_te), batch_size=batch, shuffle=False)
    opt  = optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
    crit = nn.HuberLoss(delta=1.0)
    sch  = optim.lr_scheduler.ReduceLROnPlateau(
               opt, mode="min", factor=0.5, patience=15, min_lr=1e-6)
    best_vl, pc, best_st = float("inf"), 0, None
    tr_h, vl_h = [], []

    for ep in range(1, epochs+1):
        model.train()
        ep_l = 0.0
        for bx, by in loader_tr:
            opt.zero_grad()
            loss = crit(model(bx), by)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            ep_l += loss.item()
        tr_avg = ep_l / len(loader_tr)

        model.eval()
        with torch.no_grad():
            vl_avg = sum(crit(model(bx), by).item()
                         for bx, by in loader_te) / len(loader_te)
        sch.step(vl_avg)
        tr_h.append(tr_avg); vl_h.append(vl_avg)

        if vl_avg < best_vl - 1e-6:
            best_vl, pc = vl_avg, 0
            best_st = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            pc += 1
            if pc >= patience and ep >= min_epochs:
                print(f"    [{label}] Early stop @ ep {ep}  "
                      f"best_val={best_vl:.5f}  "
                      f"lr={opt.param_groups[0]['lr']:.2e}")
                break
        if ep % 50 == 0 or ep == 1:
            print(f"    [{label}] ep {ep:3d}  "
                  f"train={tr_avg:.5f}  val={vl_avg:.5f}  "
                  f"lr={opt.param_groups[0]['lr']:.2e}")

    model.load_state_dict(best_st)
    return tr_h, vl_h


def inv_log_units(scaled_pred, sc, col_idx=0):
    dummy = np.zeros((len(scaled_pred), N_FEAT))
    dummy[:, col_idx] = scaled_pred.ravel()
    log_pred = sc.inverse_transform(dummy)[:, col_idx]
    return np.expm1(log_pred)


def calc_metrics(actual, pred):
    mae  = mean_absolute_error(actual, pred)
    rmse = np.sqrt(mean_squared_error(actual, pred))
    eps  = np.abs(actual).mean() * 0.01 + 1e-6
    mape = np.mean(np.abs((actual - pred) / (np.abs(actual) + eps))) * 100
    r2   = r2_score(actual, pred)
    mbd  = np.mean(actual - pred)
    nr   = np.sqrt(mean_squared_error(actual[1:], actual[:-1]))
    thu  = rmse / nr if nr > 0 else np.inf
    da   = np.mean(np.sign(actual[1:]-actual[:-1]) ==
                   np.sign(pred[1:]-pred[:-1])) * 100
    return dict(MAE=mae, RMSE=rmse, MAPE=mape, R2=r2,
                MBD=mbd, Theils_U=thu, Dir_Acc=da)


# B-3  Train full model
print("\n[B-3] Training DemandForecastingModel on POOLED data ...")
lstm_model = DemandForecastingModel().to(DEVICE)
tr_losses, vl_losses = train_model(
    lstm_model, X_tr, y_tr, X_te, y_te, label="Full")
lstm_model.eval()


# B-4  Evaluate on POOLED test set
print("\n[B-4] Pooled test set evaluation ...")
all_actual_real, all_pred_real = [], []
for sc, (Xp, yp, sclr) in product_test_info.items():
    Xp_t = torch.from_numpy(Xp).to(DEVICE)
    with torch.no_grad():
        pr = lstm_model(Xp_t).cpu().numpy()
    all_actual_real.append(inv_log_units(yp,   sclr))
    all_pred_real.append(  inv_log_units(pr,   sclr))

actuals_pool = np.concatenate(all_actual_real)
preds_pool   = np.concatenate(all_pred_real)
m_full       = calc_metrics(actuals_pool, preds_pool)
resid        = actuals_pool - preds_pool
mu_r, std_r  = np.mean(resid), np.std(resid)

print(f"\n  Pooled test  MAE={m_full['MAE']:.2f}  RMSE={m_full['RMSE']:.2f}  "
      f"MAPE={m_full['MAPE']:.1f}%  R2={m_full['R2']:.3f}  "
      f"Dir_Acc={m_full['Dir_Acc']:.1f}%")


# B-5  Per-product metrics
print("\n[B-5] Per-product metrics ...")
per_prod_metrics = {}
for sc, (Xp, yp, sclr) in product_test_info.items():
    Xp_t = torch.from_numpy(Xp).to(DEVICE)
    with torch.no_grad():
        pr = lstm_model(Xp_t).cpu().numpy()
    act_r = inv_log_units(yp, sclr)
    prd_r = inv_log_units(pr, sclr)
    per_prod_metrics[sc] = calc_metrics(act_r, prd_r)

best_sc    = max(per_prod_metrics, key=lambda s: per_prod_metrics[s]["R2"])
r2_values  = [v["R2"] for v in per_prod_metrics.values()]
print(f"  Best  product : {best_sc}   R2={per_prod_metrics[best_sc]['R2']:.3f}")
print(f"  Mean R2 across all {n_train_prod} products: {np.mean(r2_values):.3f}")
print(f"  Products with R2 > 0   : {sum(1 for v in r2_values if v > 0)}/{n_train_prod}")
print(f"  Products with R2 > 0.3 : {sum(1 for v in r2_values if v > 0.3)}/{n_train_prod}")

# Use best product for paper figure
viz_sc   = best_sc
viz_data = product_test_info[viz_sc]
Xv_t     = torch.from_numpy(viz_data[0]).to(DEVICE)
with torch.no_grad():
    pv_s = lstm_model(Xv_t).cpu().numpy()
actuals_viz = inv_log_units(viz_data[1], viz_data[2])
preds_viz   = inv_log_units(pv_s,        viz_data[2])
m_viz       = per_prod_metrics[viz_sc]
resid_viz   = actuals_viz - preds_viz
mu_v, std_v = np.mean(resid_viz), np.std(resid_viz)


# =============================================================================
#  BLOCK C  FIGURES
# =============================================================================
print("\n" + "=" * 68)
print("  BLOCK C -- SAVING FIGURES")
print("=" * 68)

# Figure 1 -- Training & Validation Loss
fig, ax = plt.subplots(figsize=(7.5, 3.8))
ep_x = np.arange(1, len(tr_losses)+1)
ax.plot(ep_x, tr_losses, color="#1565C0", lw=1.8, label="Training Loss")
ax.plot(ep_x, vl_losses, color="#B71C1C", lw=1.8, ls="--", label="Validation Loss")
ax.fill_between(ep_x, tr_losses, vl_losses, alpha=0.07, color="#B71C1C")
ax.set_xlabel("Epoch"); ax.set_ylabel("Huber Loss")
ax.set_title(f"Fig 1 -- Training vs Validation Loss\n"
             f"Pooled {n_train_prod}-product  |  "
             f"{X_tr.shape[0]:,} sequences  |  {N_FEAT} features")
ax.legend(); ax.grid(True, ls=":", alpha=0.45)
ax.yaxis.set_major_formatter(mtick.FormatStrFormatter("%.4f"))
plt.tight_layout()
plt.savefig(f"{RESULTS_DIR}/fig1_loss_curve.png", dpi=300)
plt.close()
print("  Fig 1 saved")

# Figure 2 -- Forecast Quality (best product, 3-panel)
fig = plt.figure(figsize=(14, 9))
gs  = fig.add_gridspec(2, 2, hspace=0.40, wspace=0.32)
ax0 = fig.add_subplot(gs[0, :])
ax1 = fig.add_subplot(gs[1, 0])
ax2 = fig.add_subplot(gs[1, 1])

n_show = min(len(actuals_viz), 120)
ax0.plot(actuals_viz[:n_show], color="#1565C0", lw=1.4, label="Actual Demand")
ax0.plot(preds_viz[:n_show],   color="#B71C1C", lw=1.4, ls="--", label="LSTM Forecast")
ax0.set_title(f"Actual vs Predicted  (product {viz_sc}, {n_show} test days)  "
              f"R2={m_viz['R2']:.3f}  MAPE={m_viz['MAPE']:.1f}%")
ax0.set_ylabel("Units Sold"); ax0.legend(); ax0.grid(True, ls=":", alpha=0.45)

lim = (min(actuals_viz.min(), preds_viz.min())-1,
       max(actuals_viz.max(), preds_viz.max())+1)
ax1.scatter(actuals_viz, preds_viz, alpha=0.45, s=18,
            color="#1a237e", edgecolors="none")
ax1.plot(lim, lim, "r--", lw=1.5, label="Perfect fit")
ax1.set(xlim=lim, ylim=lim, title="Predicted vs Actual (Test Set)",
        xlabel="Actual Units Sold", ylabel="Predicted Units Sold")
ax1.text(0.05, 0.90, f"R2 = {m_viz['R2']:.3f}", transform=ax1.transAxes,
         fontsize=10, bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7))
ax1.legend(); ax1.grid(True, ls=":", alpha=0.45)

xr = np.linspace(resid_viz.min(), resid_viz.max(), 300)
ax2.hist(resid_viz, bins=25, color="#2E7D32", edgecolor="white",
         alpha=0.75, density=True, label="Residuals")
ax2.plot(xr, stats.norm.pdf(xr, mu_v, std_v), "k-", lw=1.8, label="Normal fit")
ax2.axvline(0, color="red", lw=1.2, ls="--")
ax2.set(title="Residual Distribution",
        xlabel="Residual (Actual minus Predicted)", ylabel="Density")
ax2.legend(); ax2.grid(True, ls=":", alpha=0.45)
plt.suptitle(f"Fig 2 -- LSTM Demand Forecasting (Best Product: {viz_sc})\n"
             f"Pooled R2={m_full['R2']:.3f}  |  "
             f"Mean R2={np.mean(r2_values):.3f}",
             fontsize=11, fontweight="bold", y=1.01)
plt.savefig(f"{RESULTS_DIR}/fig2_forecast_quality.png", dpi=300)
plt.close()
print("  Fig 2 saved")


# =============================================================================
#  BLOCK D  SAVE PRODUCTION WEIGHTS
# =============================================================================
print("\n" + "=" * 68)
print("  BLOCK D -- SAVING PRODUCTION WEIGHTS")
print("=" * 68)

torch.save(lstm_model.state_dict(), f"{RESULTS_DIR}/demand_model.pt")
torch.save({
    "model_state_dict" : lstm_model.state_dict(),
    "model_class"      : "DemandForecastingModel",
    "input_dim"        : N_FEAT,
    "hidden1"          : 64,
    "hidden2"          : 32,
    "seq_len"          : SEQ_LEN,
    "dropout"          : 0.30,
    "features"         : FEATURES,
    "target_transform" : "log1p / expm1",
    "normalisation"    : "per-product Z-score StandardScaler",
    "n_train_products" : n_train_prod,
    "metrics_pooled"   : m_full,
    "metrics_best_prod": m_viz,
    "dataset"          : "UCI Online Retail II UK",
    "saved_at"         : datetime.now().isoformat(),
}, f"{RESULTS_DIR}/demand_model_checkpoint.pt")

with open(f"{RESULTS_DIR}/product_scalers.pkl", "wb") as fh:
    pickle.dump(product_scalers, fh)

# Save metrics to a text report
with open(f"{RESULTS_DIR}/metrics_report.txt", "w") as f:
    f.write("=" * 68 + "\n")
    f.write("  V5 TRAINING RESULTS -- UCI Online Retail II\n")
    f.write("=" * 68 + "\n\n")
    f.write(f"Dataset          : {DATA_PATH}\n")
    f.write(f"Products trained : {n_train_prod}\n")
    f.write(f"Train sequences  : {X_tr.shape[0]:,}\n")
    f.write(f"Test  sequences  : {X_te.shape[0]:,}\n")
    f.write(f"Model params     : {n_params:,}\n\n")
    f.write("POOLED TEST METRICS:\n")
    for k, v in m_full.items():
        f.write(f"  {k:15s} : {v:.4f}\n")
    f.write(f"\nMean R2 across all products : {np.mean(r2_values):.4f}\n")
    f.write(f"Products with R2 > 0       : {sum(1 for v in r2_values if v > 0)}/{n_train_prod}\n")
    f.write(f"Products with R2 > 0.3     : {sum(1 for v in r2_values if v > 0.3)}/{n_train_prod}\n")
    f.write(f"Products with R2 > 0.5     : {sum(1 for v in r2_values if v > 0.5)}/{n_train_prod}\n")
    f.write(f"\nBest product: {best_sc}  R2={per_prod_metrics[best_sc]['R2']:.4f}\n")

print(f"""
  SAVED:
    {RESULTS_DIR}/demand_model.pt              <-- PRODUCTION WEIGHTS
    {RESULTS_DIR}/demand_model_checkpoint.pt   <-- full metadata
    {RESULTS_DIR}/product_scalers.pkl          <-- per-product scalers
    {RESULTS_DIR}/metrics_report.txt           <-- text metrics
    {RESULTS_DIR}/fig1_loss_curve.png          <-- loss curve
    {RESULTS_DIR}/fig2_forecast_quality.png    <-- forecast quality
""")

print("=" * 68)
print("  PIPELINE COMPLETE -- V5 Pooled Multi-Product Real Data")
print(f"  Pooled R2={m_full['R2']:.3f}  "
      f"Best-product R2={m_viz['R2']:.3f}  "
      f"Mean-R2={np.mean(r2_values):.3f}")
print("=" * 68)
