import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import os


def compute_metrics(actual, pred):
    """Compute regression metrics."""
    actual = np.array(actual).flatten()
    pred = np.array(pred).flatten()

    mae = mean_absolute_error(actual, pred)
    rmse = np.sqrt(mean_squared_error(actual, pred))
    r2 = r2_score(actual, pred)

    # Safe MAPE (avoid division by zero)
    mask = actual != 0
    if mask.sum() > 0:
        mape = np.mean(np.abs((actual[mask] - pred[mask]) / actual[mask])) * 100
    else:
        mape = 0.0

    return {
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "R2": round(r2, 4),
        "MAPE": round(mape, 2)
    }


def plot_r2_score(r2, output_dir="outputs", iteration=None):
    """Create a bar chart of R2 score with target range highlighted."""
    os.makedirs(output_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))

    # Target range band
    ax.axhspan(0.5, 0.8, alpha=0.15, color="green", label="Target Range (0.5 - 0.8)")

    # Bar
    color = "green" if 0.5 <= r2 <= 0.8 else "red"
    bar_label = f"R² = {r2:.4f}"
    ax.bar(["HybridTransformer-LSTM"], [r2], color=color, width=0.4, edgecolor="black")
    ax.text(0, r2 + 0.02, bar_label, ha="center", va="bottom", fontsize=14, fontweight="bold")

    ax.set_ylim(0, max(1.0, r2 + 0.15))
    ax.set_ylabel("R² Score", fontsize=12)
    title = "Model R² Score"
    if iteration is not None:
        title += f" (Iteration {iteration})"
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axhline(y=0.5, color="orange", linestyle="--", alpha=0.6)
    ax.axhline(y=0.8, color="orange", linestyle="--", alpha=0.6)
    ax.legend(loc="upper right")

    plt.tight_layout()
    fname = os.path.join(output_dir, "r2_score.png")
    fig.savefig(fname, dpi=150)
    plt.close(fig)
    print(f"  R² plot saved to {fname}")
    return fname


def plot_predictions(actual, pred, output_dir="outputs", n_points=200):
    """Plot actual vs predicted values."""
    os.makedirs(output_dir, exist_ok=True)

    actual = np.array(actual).flatten()[:n_points]
    pred = np.array(pred).flatten()[:n_points]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Time series view
    axes[0].plot(actual, label="Actual", alpha=0.8, linewidth=1.2)
    axes[0].plot(pred, label="Predicted", alpha=0.8, linewidth=1.2)
    axes[0].set_xlabel("Sample Index")
    axes[0].set_ylabel("log(units_sold + 1)")
    axes[0].set_title("Actual vs Predicted (Time Series)")
    axes[0].legend()

    # Scatter plot
    axes[1].scatter(actual, pred, alpha=0.4, s=10)
    mn, mx = min(actual.min(), pred.min()), max(actual.max(), pred.max())
    axes[1].plot([mn, mx], [mn, mx], "r--", linewidth=1.5, label="Perfect Fit")
    axes[1].set_xlabel("Actual")
    axes[1].set_ylabel("Predicted")
    axes[1].set_title("Scatter: Actual vs Predicted")
    axes[1].legend()

    plt.tight_layout()
    fname = os.path.join(output_dir, "predictions.png")
    fig.savefig(fname, dpi=150)
    plt.close(fig)
    print(f"  Predictions plot saved to {fname}")
    return fname


def plot_training_history(history, output_dir="outputs"):
    """Plot training and validation loss curves."""
    os.makedirs(output_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(history["train_losses"], label="Train Loss", alpha=0.8)
    ax.plot(history["val_losses"], label="Val Loss", alpha=0.8)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.set_title("Training History")
    ax.legend()

    plt.tight_layout()
    fname = os.path.join(output_dir, "training_history.png")
    fig.savefig(fname, dpi=150)
    plt.close(fig)
    print(f"  Training history plot saved to {fname}")
    return fname