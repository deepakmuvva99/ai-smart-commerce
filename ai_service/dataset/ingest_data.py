import sqlite3
import pandas as pd
import os
from datetime import datetime

def ingest_real_data(db_path, output_dir='.'):
    """
    Connects to the SQLite database, extracts real sales/traffic data,
    and formats it into a continuous daily timeseries per product 
    for the AI demand forecasting model.
    """
    print(f"Connecting to database at {db_path}...")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    
    # 1. Fetch products
    products_df = pd.read_sql_query("SELECT id as Product_ID, base_price as Base_Price, current_price as Current_Price FROM products", conn)
    
    # 2. Fetch traffic views per product per day
    traffic_df = pd.read_sql_query("""
        SELECT product_id as Product_ID, date(timestamp) as Date, count(*) as Traffic_Views 
        FROM traffic_logs 
        GROUP BY product_id, date(timestamp)
    """, conn)
    
    # 3. Fetch daily demand (quantity sold) per product
    orders_df = pd.read_sql_query("""
        SELECT pv.product_id as Product_ID, date(o.created_at) as Date, sum(oi.quantity) as Demand_Units
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN product_variants pv ON oi.variant_id = pv.id
        GROUP BY pv.product_id, date(o.created_at)
    """, conn)
    
    conn.close()
    
    if traffic_df.empty and orders_df.empty:
        print("No traffic or order data found in the database. Returning early.")
        return
        
    # Get the overall date range in the dataset
    dates = []
    if not traffic_df.empty:
        dates.extend(pd.to_datetime(traffic_df['Date']).tolist())
    if not orders_df.empty:
        dates.extend(pd.to_datetime(orders_df['Date']).tolist())
        
    if not dates:
        print("No valid timestamps found.")
        return
        
    min_date = min(dates)
    max_date = max(dates)
    
    # Create a full calendar date range
    date_range = pd.date_range(start=min_date, end=max_date)
    
    # Generate every combination of Date and Product_ID
    all_combinations = [(d.strftime('%Y-%m-%d'), p) for d in date_range for p in products_df['Product_ID']]
    base_df = pd.DataFrame(all_combinations, columns=['Date', 'Product_ID'])
    base_df['Date'] = pd.to_datetime(base_df['Date'])
    
    # Merge Products
    result_df = pd.merge(base_df, products_df, on='Product_ID', how='left')
    
    # Merge Traffic Data
    if not traffic_df.empty:
        traffic_df['Date'] = pd.to_datetime(traffic_df['Date'])
        result_df = pd.merge(result_df, traffic_df, on=['Product_ID', 'Date'], how='left')
    else:
        result_df['Traffic_Views'] = 0
        
    # Merge Orders Data
    if not orders_df.empty:
        orders_df['Date'] = pd.to_datetime(orders_df['Date'])
        result_df = pd.merge(result_df, orders_df, on=['Product_ID', 'Date'], how='left')
    else:
        result_df['Demand_Units'] = 0
        
    # Fill NAs with 0 (days with no traffic or sales)
    result_df['Traffic_Views'] = result_df['Traffic_Views'].fillna(0).astype(int)
    result_df['Demand_Units'] = result_df['Demand_Units'].fillna(0).astype(int)
    
    # Calculate Day_Of_Week feature needed by the model
    result_df['Day_Of_Week'] = result_df['Date'].dt.dayofweek
    result_df['Date'] = result_df['Date'].dt.strftime('%Y-%m-%d')
    
    # Order columns
    result_df = result_df[['Date', 'Product_ID', 'Base_Price', 'Current_Price', 'Day_Of_Week', 'Traffic_Views', 'Demand_Units']]
    
    # Save Output
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, 'real_demand_data.csv')
    result_df.to_csv(out_path, index=False)
    
    print(f"Successfully ingested {len(result_df)} records into {out_path}.")
    print(result_df.head(10))

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, '..', '..'))
    db_path = os.path.join(root_dir, 'sql_app.db')
    
    ingest_real_data(db_path=db_path, output_dir=script_dir)
