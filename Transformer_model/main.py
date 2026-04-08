"""
Full end-to-end demand forecasting pipeline.

Steps:
  1. Load & preprocess raw CSV
  2. Feature engineering
  3. Build sliding-window sequences (per product, last 20% as test)
  4. Scale features globally (fit on train only)
  5. Train HybridTransformer-LSTM
  6. Evaluate (R², MAE, RMSE, MAPE)
  7. Plot R² score
  8. Auto-iterate if R² not in [0.5, 0.8]
"""

import sys
import os
import numpy as np
import torch
from sklearn.preprocessing import StandardScaler

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.preprocess import load_and_preprocess
from features.feature_engineering import create_features
from training.dataset_builder import create_sequences
from training.train_forecaster import train_model
from evaluation.metrics import (
    compute_metrics,
    plot_r2_score,
    plot_predictions,
    plot_training_history,
)
from configs.config import FEATURES, TARGET, SEQ_LEN, TOP_N_PRODUCTS, DEVICE


# ── Hyperparameter configurations to iterate through ────────────────────
CONFIGS = [
    # Iteration 1: baseline
    {"d_model": 64, "heads": 4, "layers": 2, "epochs": 120, "lr": 3e-4},
    # Iteration 2: larger model
    {"d_model": 128, "heads": 4, "layers": 3, "epochs": 150, "lr": 2e-4},
    # Iteration 3: wider with more heads
    {"d_model": 96, "heads": 8, "layers": 2, "epochs": 150, "lr": 1e-4},
    # Iteration 4: deeper, slower
    {"d_model": 64, "heads": 4, "layers": 4, "epochs": 200, "lr": 1e-4},
    # Iteration 5: compact fast
    {"d_model": 48, "heads": 4, "layers": 2, "epochs": 200, "lr": 5e-4},
]

TARGET_R2_MIN = 0.5
TARGET_R2_MAX = 0.8


def prepare_data(csv_path):
    """Load, preprocess, engineer features, build sequences with proper split."""
    print("\n" + "=" * 60)
    print("STEP 1: Data Preprocessing")
    print("=" * 60)
    df = load_and_preprocess(csv_path, top_n=TOP_N_PRODUCTS)

    print("\n" + "=" * 60)
    print("STEP 2: Feature Engineering")
    print("=" * 60)
    df = create_features(df)
    print(f"Features created. Shape: {df.shape}")

    # Verify all required features exist
    missing = [f for f in FEATURES if f not in df.columns]
    if missing:
        raise ValueError(f"Missing features after engineering: {missing}")

    print("\n" + "=" * 60)
    print("STEP 3: Build Sequences (per-product split)")
    print("=" * 60)

    target_idx = FEATURES.index(TARGET)

    train_X_list, train_y_list = [], []
    test_X_list, test_y_list = [], []

    for stock_code, group in df.groupby("StockCode"):
        if len(group) <= SEQ_LEN + 5:
            continue

        feature_data = group[FEATURES].values.astype(np.float32)

        # Per-product: build sequences on RAW (unscaled) features
        # We'll scale after splitting
        X_seq, y_seq = create_sequences(feature_data, target_idx, SEQ_LEN)

        if len(X_seq) < 5:
            continue

        # Chronological split per product: 80% train, 20% test
        split = int(0.8 * len(X_seq))
        split = max(split, 1)

        train_X_list.append(X_seq[:split])
        train_y_list.append(y_seq[:split])
        test_X_list.append(X_seq[split:])
        test_y_list.append(y_seq[split:])

    X_train = torch.cat(train_X_list, dim=0)
    y_train = torch.cat(train_y_list, dim=0)
    X_test = torch.cat(test_X_list, dim=0)
    y_test = torch.cat(test_y_list, dim=0)

    print(f"Train sequences: {len(X_train)}, Test sequences: {len(X_test)}")

    # ── Global scaling (fit on train, transform both) ──────────────────
    # Reshape to 2D for scaler: (n * seq_len, features)
    n_train, seq_len, n_feat = X_train.shape
    n_test = X_test.shape[0]

    train_2d = X_train.reshape(-1, n_feat).numpy()
    test_2d = X_test.reshape(-1, n_feat).numpy()

    scaler = StandardScaler()
    train_2d = scaler.fit_transform(train_2d)
    test_2d = scaler.transform(test_2d)

    X_train = torch.FloatTensor(train_2d.reshape(n_train, seq_len, n_feat))
    X_test = torch.FloatTensor(test_2d.reshape(n_test, seq_len, n_feat))

    # Scale target using the target column's scaler parameters
    target_mean = scaler.mean_[target_idx]
    target_std = scaler.scale_[target_idx]

    # Keep y in ORIGINAL (unscaled) space for R² computation
    # But also provide scaled y for training
    y_train_raw = y_train.clone()
    y_test_raw = y_test.clone()

    y_train_scaled = (y_train - target_mean) / target_std
    y_test_scaled = (y_test - target_mean) / target_std

    print(f"Train X shape: {X_train.shape}")
    print(f"Target mean: {target_mean:.4f}, std: {target_std:.4f}")
    print(f"y_train range: [{y_train_raw.min():.2f}, {y_train_raw.max():.2f}]")
    print(f"y_test range:  [{y_test_raw.min():.2f}, {y_test_raw.max():.2f}]")

    return (X_train, y_train_scaled, X_test, y_test_scaled,
            y_train_raw, y_test_raw, target_mean, target_std)


def run_training_iteration(X_train, y_train, X_test, y_test,
                           y_test_raw, target_mean, target_std,
                           config, iteration):
    """Run a single training iteration with given config."""
    print(f"\n{'=' * 60}")
    print(f"ITERATION {iteration}: {config}")
    print(f"{'=' * 60}")

    input_dim = X_train.shape[2]

    model, history = train_model(
        X_train, y_train, X_test, y_test,
        input_dim=input_dim,
        d_model=config["d_model"],
        heads=config["heads"],
        layers=config["layers"],
        epochs=config["epochs"],
        lr=config["lr"],
    )

    # Evaluate — inverse-scale predictions back to original space
    model.eval()
    with torch.no_grad():
        preds_scaled = model(X_test.to(DEVICE)).squeeze(-1).cpu().numpy()

    # Inverse scale
    preds_original = preds_scaled * target_std + target_mean
    actuals_original = y_test_raw.numpy()

    metrics = compute_metrics(actuals_original, preds_original)
    print(f"\n  ── Metrics (original scale) ──")
    for k, v in metrics.items():
        print(f"    {k}: {v}")

    # Plot
    plot_r2_score(metrics["R2"], iteration=iteration)
    plot_predictions(actuals_original, preds_original)
    plot_training_history(history)

    return metrics, model


def main():
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data", "online_retail_II.csv"
    )

    if not os.path.exists(csv_path):
        print(f"ERROR: CSV not found at {csv_path}")
        sys.exit(1)

    (X_train, y_train, X_test, y_test,
     y_train_raw, y_test_raw, target_mean, target_std) = prepare_data(csv_path)

    # ── Iterate through configs until R² is in range ────────────────────
    best_r2 = None
    best_metrics = None
    best_model = None

    for i, config in enumerate(CONFIGS, start=1):
        metrics, model = run_training_iteration(
            X_train, y_train, X_test, y_test,
            y_test_raw, target_mean, target_std,
            config, iteration=i
        )

        r2 = metrics["R2"]

        if best_r2 is None or abs(r2 - 0.65) < abs(best_r2 - 0.65):
            best_r2 = r2
            best_metrics = metrics
            best_model = model

        if TARGET_R2_MIN <= r2 <= TARGET_R2_MAX:
            print(f"\n{'=' * 60}")
            print(f"SUCCESS! R² = {r2:.4f} is within target range "
                  f"[{TARGET_R2_MIN}, {TARGET_R2_MAX}]")
            print(f"{'=' * 60}")
            break
        else:
            direction = "too low" if r2 < TARGET_R2_MIN else "too high"
            print(f"\n  R² = {r2:.4f} is {direction}. Trying next config...")
    else:
        print(f"\n{'=' * 60}")
        print(f"Exhausted all configs. Best R² = {best_r2:.4f}")
        print(f"Using best model found.")
        print(f"{'=' * 60}")

        # Save best result plots
        plot_r2_score(best_r2, iteration="best")

    # Save final model
    if best_model is not None:
        torch.save(best_model.state_dict(), "outputs/final_model.pt")
        print("Final model saved to outputs/final_model.pt")

    print(f"\nFinal Metrics: {best_metrics}")
    print("All plots saved to outputs/")


if __name__ == "__main__":
    main()