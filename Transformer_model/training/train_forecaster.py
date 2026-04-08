import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import os

from models.hybrid_transformer_lstm import HybridDemandModel
from evaluation.metrics import compute_metrics
from configs.config import BATCH_SIZE, LR, EPOCHS, PATIENCE, DEVICE


def train_model(X_train, y_train, X_val, y_val, input_dim=15,
                d_model=64, heads=4, layers=2, epochs=None, lr=None):
    """
    Train the HybridDemandModel with early stopping.

    Returns:
        model: trained model
        history: dict with train_losses, val_losses
    """
    device = DEVICE
    _epochs = epochs or EPOCHS
    _lr = lr or LR

    model = HybridDemandModel(
        input_dim=input_dim,
        d_model=d_model,
        heads=heads,
        layers=layers
    ).to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=_lr,
        weight_decay=1e-4
    )

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=10
    )

    criterion = nn.HuberLoss()

    train_loader = DataLoader(
        TensorDataset(X_train, y_train),
        batch_size=BATCH_SIZE,
        shuffle=True
    )

    history = {"train_losses": [], "val_losses": []}
    best_val_loss = float("inf")
    patience_counter = 0
    best_model_state = None

    for epoch in range(_epochs):

        # --- Train ---
        model.train()
        total_loss = 0
        n_batches = 0

        for bx, by in train_loader:
            bx = bx.to(device)
            by = by.to(device)

            optimizer.zero_grad()
            pred = model(bx).squeeze(-1)
            loss = criterion(pred, by)
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            total_loss += loss.item()
            n_batches += 1

        avg_train_loss = total_loss / max(n_batches, 1)
        history["train_losses"].append(avg_train_loss)

        # --- Validate ---
        model.eval()
        with torch.no_grad():
            val_pred = model(X_val.to(device)).squeeze(-1)
            val_loss = criterion(val_pred, y_val.to(device)).item()

        history["val_losses"].append(val_loss)
        scheduler.step(val_loss)

        if epoch % 10 == 0 or epoch == _epochs - 1:
            print(f"  Epoch {epoch:3d}/{_epochs}  "
                  f"train_loss={avg_train_loss:.4f}  val_loss={val_loss:.4f}")

        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= PATIENCE:
                print(f"  Early stopping at epoch {epoch}")
                break

    # Load best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)

    # Save checkpoint
    os.makedirs("outputs", exist_ok=True)
    torch.save(model.state_dict(), "outputs/best_model.pt")
    print("  Model saved to outputs/best_model.pt")

    return model, history