import torch

SEQ_LEN = 21

FEATURES = [
    "log_units_sold",
    "current_price",
    "num_invoices",
    "basket_size",
    "promotion_flag",
    "price_volatility_7d",
    "days_since_last",
    "day_of_week",
    "inventory_level",
    "rolling_mean_7",
    "rolling_mean_14",
    "rolling_std_7",
    "price_change",
    "price_ratio",
    "trend_signal"
]

TARGET = "log_units_sold"

TOP_N_PRODUCTS = 50

BATCH_SIZE = 512
LR = 3e-4
EPOCHS = 100
PATIENCE = 30

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"