import pandas as pd
import numpy as np


def create_features(df):
    """
    Create derived features for demand forecasting.
    Expects a DataFrame with columns: StockCode, date, units_sold,
    current_price, base_price, num_invoices, basket_size, etc.
    """
    df = df.sort_values(["StockCode", "date"]).copy()

    # Rolling statistics on units_sold
    df["rolling_mean_7"] = (
        df.groupby("StockCode")["units_sold"]
        .transform(lambda x: x.rolling(7, min_periods=1).mean())
    )

    df["rolling_mean_14"] = (
        df.groupby("StockCode")["units_sold"]
        .transform(lambda x: x.rolling(14, min_periods=1).mean())
    )

    df["rolling_std_7"] = (
        df.groupby("StockCode")["units_sold"]
        .transform(lambda x: x.rolling(7, min_periods=1).std().fillna(0))
    )

    # Price features
    df["price_change"] = (
        df.groupby("StockCode")["current_price"]
        .pct_change()
        .fillna(0)
    )

    df["price_ratio"] = df["current_price"] / df["base_price"].replace(0, 1)

    # Trend signal
    df["trend_signal"] = df["units_sold"] - df["rolling_mean_7"]

    # Log transform target
    df["log_units_sold"] = np.log1p(df["units_sold"])

    # Clip extreme values
    for col in df.select_dtypes(include=[np.number]).columns:
        df[col] = df[col].replace([np.inf, -np.inf], np.nan)

    df = df.fillna(0)

    return df