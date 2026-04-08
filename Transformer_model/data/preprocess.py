import pandas as pd
import numpy as np


def load_and_preprocess(csv_path, top_n=50):
    """
    Load raw Online Retail II CSV and transform into daily per-product
    aggregated data suitable for demand forecasting.
    """
    print("Loading raw data...")
    df = pd.read_csv(csv_path)

    # --- Clean ---
    df = df.dropna(subset=["Customer ID"])
    df = df[~df["Invoice"].astype(str).str.startswith("C")]  # remove cancellations
    df = df[df["Quantity"] > 0]
    df = df[df["Price"] > 0]

    # Parse dates
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["date"] = df["InvoiceDate"].dt.date

    # --- Aggregate to daily per StockCode ---
    daily = df.groupby(["StockCode", "date"]).agg(
        units_sold=("Quantity", "sum"),
        current_price=("Price", "mean"),
        num_invoices=("Invoice", "nunique"),
        basket_size=("Quantity", "mean"),
    ).reset_index()

    daily["date"] = pd.to_datetime(daily["date"])

    # --- Filter to top N products by total volume ---
    top_products = (
        daily.groupby("StockCode")["units_sold"]
        .sum()
        .nlargest(top_n)
        .index
    )
    daily = daily[daily["StockCode"].isin(top_products)].copy()
    print(f"Filtered to top {top_n} products: {len(daily)} daily records")

    # --- Derive base_price (median price per product over full period) ---
    base_prices = daily.groupby("StockCode")["current_price"].median()
    daily["base_price"] = daily["StockCode"].map(base_prices)

    # --- Derive price_volatility_7d ---
    daily = daily.sort_values(["StockCode", "date"])
    daily["price_volatility_7d"] = (
        daily.groupby("StockCode")["current_price"]
        .transform(lambda x: x.rolling(7, min_periods=1).std().fillna(0))
    )

    # --- Derive days_since_last ---
    daily["days_since_last"] = (
        daily.groupby("StockCode")["date"]
        .diff()
        .dt.days
        .fillna(0)
    )

    # --- day_of_week ---
    daily["day_of_week"] = daily["date"].dt.dayofweek

    # --- inventory_level (synthetic: starting stock - cumulative sales) ---
    max_daily = daily.groupby("StockCode")["units_sold"].max()
    starting_stock = daily["StockCode"].map(max_daily) * 30  # rough estimate
    daily["inventory_level"] = (
        starting_stock
        - daily.groupby("StockCode")["units_sold"].cumsum()
    )
    daily["inventory_level"] = daily["inventory_level"].clip(lower=0)

    # --- promotion_flag (1 if current_price < 0.9 * base_price) ---
    daily["promotion_flag"] = (
        (daily["current_price"] < 0.9 * daily["base_price"]).astype(int)
    )

    # Fill any remaining NaN
    daily = daily.fillna(0)

    print(f"Preprocessing complete. Shape: {daily.shape}")
    return daily
