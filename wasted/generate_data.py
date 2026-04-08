import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_synthetic_data(num_days=60, num_products=50, output_dir='.'):
    """
    Generates a synthetic e-commerce dataset for demand forecasting.
    Outputs a CSV with features: Date, Product_ID, Base_Price, Current_Price, Traffic_Views, Day_Of_Week, and the label: Demand_Units
    """
    print(f"Generating synthetic data for {num_products} products over {num_days} days...")
    
    start_date = datetime.today() - timedelta(days=num_days)
    dates = [start_date + timedelta(days=i) for i in range(num_days)]
    
    data = []
    
    # Define product baselines
    np.random.seed(42) # For reproducibility
    products = []
    for p_id in range(1, num_products + 1):
        base_price = np.random.uniform(10.0, 500.0)
        base_demand = np.random.uniform(5, 50)
        price_elasticity = np.random.uniform(-2.5, -0.5) # How much demand changes with price
        seasonality_factor = np.random.uniform(0.8, 1.2)
        products.append({
            'id': p_id,
            'base_price': base_price,
            'base_demand': base_demand,
            'elasticity': price_elasticity,
            'seasonality': seasonality_factor
        })

    for date in dates:
        day_of_week = date.weekday()
        # Weekend bump
        weekend_multiplier = 1.3 if day_of_week >= 5 else 1.0
        
        for p in products:
            # Randomly fluctuate the price around the base price
            price_variance = np.random.uniform(0.85, 1.15)
            current_price = p['base_price'] * price_variance
            
            # Traffic is correlated with base demand but has noise
            traffic_views = int(p['base_demand'] * np.random.uniform(5, 15) * weekend_multiplier)
            
            # Demand calculation:
            # Base * (Price change effect given elasticity) * weekend * seasonality * noise
            price_ratio = current_price / p['base_price']
            price_effect = price_ratio ** p['elasticity']
            
            expected_demand = p['base_demand'] * price_effect * weekend_multiplier * p['seasonality']
            
            # Add Poisson noise to simulate realistic integer bounds
            actual_demand = np.random.poisson(expected_demand)
            
            data.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Product_ID': p['id'],
                'Base_Price': round(p['base_price'], 2),
                'Current_Price': round(current_price, 2),
                'Day_Of_Week': day_of_week,
                'Traffic_Views': traffic_views,
                'Demand_Units': actual_demand
            })
            
    df = pd.DataFrame(data)
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, 'synthetic_demand_data.csv')
    df.to_csv(out_path, index=False)
    print(f"Data successfully generated at {out_path}")
    print(df.head())

if __name__ == "__main__":
    generate_synthetic_data(num_days=90, num_products=20, output_dir='dataset')
