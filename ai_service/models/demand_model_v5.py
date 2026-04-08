# ==============================================================================
#  FILE  : e:\DynamicPricing\smart-commerce\ai_service\models\demand_model_v5.py
# ==============================================================================
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

SEQ_LEN   = 14    # lookback window in days
N_FEAT    = 9     # number of input features

FEATURES = [
    "log_units_sold",       # [0] TARGET (log1p-transformed)
    "current_price",        # [1]
    "num_invoices",         # [2] traffic proxy
    "basket_size",          # [3]
    "promotion_flag",       # [4]
    "price_volatility_7d",  # [5]
    "days_since_last",      # [6]
    "day_of_week",          # [7]
    "inventory_level",      # [8]
]

class DemandForecastingModel(nn.Module):
    """
    BiLSTM + Attention demand forecaster.
    Trained on pooled multi-product dataset.

    Input  : (batch, 14, 9)  -- per-product Z-score normalised,
                                column 0 = log1p(units_sold)
    Output : (batch, 1)  -- Z-score normalised log1p demand

    Inference pipeline:
        1. Normalise input: StandardScaler per product (product_scalers.pkl)
        2. Forward pass -> normalised_log_pred
        3. Inverse Z-score: scaler.inverse_transform(...)[:, 0]
        4. Inverse log1p:   np.expm1(log_pred)  -> real units
    """
    def __init__(self,
                 input_dim : int   = N_FEAT,
                 hidden1   : int   = 64,
                 hidden2   : int   = 32,
                 seq_len   : int   = SEQ_LEN,
                 dropout   : float = 0.30):
        super().__init__()
        self.lstm1 = nn.LSTM(input_dim,   hidden1, batch_first=True, bidirectional=True)
        self.bn1   = nn.BatchNorm1d(seq_len)
        self.drop1 = nn.Dropout(dropout)
        self.lstm2 = nn.LSTM(hidden1 * 2, hidden2, batch_first=True, bidirectional=True)
        self.bn2   = nn.BatchNorm1d(seq_len)
        self.drop2 = nn.Dropout(dropout)
        self.attn  = nn.Linear(hidden2 * 2, 1)
        self.fc    = nn.Linear(hidden2 * 2, 1)

        for name, p in self.named_parameters():
            if "weight_ih" in name: nn.init.xavier_uniform_(p)
            elif "weight_hh" in name: nn.init.orthogonal_(p)
            elif "bias" in name: nn.init.zeros_(p)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        o1, _ = self.lstm1(x);  o1 = self.drop1(self.bn1(o1))
        o2, _ = self.lstm2(o1); o2 = self.drop2(self.bn2(o2))
        w  = torch.softmax(self.attn(o2), dim=1)
        c  = (w * o2).sum(dim=1)
        return self.fc(c)

    def get_attention_weights(self, x):
        with torch.no_grad():
            o1, _ = self.lstm1(x); o1 = self.drop1(self.bn1(o1))
            o2, _ = self.lstm2(o1); o2 = self.drop2(self.bn2(o2))
        return torch.softmax(self.attn(o2), dim=1).squeeze(-1)

def load_demand_model(weights_path: str, device: str = "cpu") -> DemandForecastingModel:
    model = DemandForecastingModel()
    state = torch.load(weights_path, map_location=device, weights_only=True)
    if isinstance(state, dict) and "model_state_dict" in state:
        state = state["model_state_dict"]
    model.load_state_dict(state)
    model.to(device)
    return model

def predict_demand(model, recent_df, product_scaler, device="cpu"):
    """
    End-to-end inference helper.

    Parameters
    ----------
    recent_df      : pd.DataFrame with last 14 rows, columns = FEATURES
    product_scaler : StandardScaler for this product (from product_scalers.pkl)
    """
    scaled = product_scaler.transform(recent_df[FEATURES])
    x = torch.from_numpy(scaled[np.newaxis].astype(np.float32)).to(device)
    model.eval()
    with torch.no_grad():
        pred_norm = model(x).cpu().numpy()    # (1, 1)
    # Reverse Z-score
    dummy = np.zeros((1, N_FEAT)); dummy[0, 0] = pred_norm.ravel()[0]
    log_pred = product_scaler.inverse_transform(dummy)[0, 0]
    # Reverse log1p
    return float(np.expm1(log_pred))
