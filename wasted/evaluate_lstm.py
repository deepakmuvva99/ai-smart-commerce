import pandas as pd
import numpy as np
import torch
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
import os

from models.demand_model import DemandForecastingModel

SEQ_LEN = 7

def evaluate_demand_model():
    print("Evaluating LSTM Demand Forecasting Model...")
    
    # Load data
    data_path = 'dataset/synthetic_demand_data.csv'
    if not os.path.exists(data_path):
        print("Dataset not found!")
        return
        
    df = pd.read_csv(data_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by=['Product_ID', 'Date'])
    
    # We will use the last 20% of data as a test set conceptually, or just evaluate on a subset
    # For a paper, we evaluate on the whole set or a holdout. Since we trained on the whole set earlier, let's just evaluate it to get the metrics.
    
    model = DemandForecastingModel(input_dim=4, hidden_dim=64, num_layers=2)
    model.load_state_dict(torch.load('exports/demand_model.pt', map_location='cpu'))
    model.eval()
    
    features = ['Base_Price', 'Current_Price', 'Day_Of_Week', 'Traffic_Views']
    
    # Normalization params (from training)
    means = df[features].mean()
    stds = df[features].std() + 1e-8
    
    df_norm = df.copy()
    for col in features:
        df_norm[col] = (df[col] - means[col]) / stds[col]
        
    actuals = []
    predictions = []
    uncertainties = []
    
    # Evaluate a sample of sequences
    for p_id in df['Product_ID'].unique()[:10]: # take first 10 products for speed
        p_data = df_norm[df_norm['Product_ID'] == p_id].reset_index(drop=True)
        raw_p_data = df[df['Product_ID'] == p_id].reset_index(drop=True)
        
        if len(p_data) <= SEQ_LEN:
            continue
            
        for i in range(len(p_data) - SEQ_LEN):
            x = p_data.loc[i:i+SEQ_LEN-1, features].values
            y_actual = raw_p_data.loc[i+SEQ_LEN, 'Demand_Units']
            
            x_tensor = torch.tensor([x], dtype=torch.float32)
            with torch.no_grad():
                mu, sigma, _ = model(x_tensor)
                
            actuals.append(y_actual)
            predictions.append(mu.item())
            uncertainties.append(sigma.item())
            
    # Calculate Academic Metrics
    mae = mean_absolute_error(actuals, predictions)
    rmse = np.sqrt(mean_squared_error(actuals, predictions))
    r2 = r2_score(actuals, predictions)
    
    # Custom MAPE to avoid div by zero
    actuals_arr = np.array(actuals)
    preds_arr = np.array(predictions)
    mask = actuals_arr > 0
    mape = np.mean(np.abs((actuals_arr[mask] - preds_arr[mask]) / actuals_arr[mask])) * 100

    print("\n" + "="*50)
    print("📊 LSTM DEMAND MODEL PERFORMANCE METRICS")
    print("="*50)
    print(f"Mean Absolute Error (MAE):       {mae:.2f} units")
    print(f"Root Mean Square Error (RMSE):   {rmse:.2f} units")
    print(f"Mean Abs Percentage Error (MAPE): {mape:.2f}%")
    print(f"Coefficient of Determination (R²): {r2:.4f}")
    
    # Generate Plots
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot 1: Predicted vs Actual Scatter
    axes[0].scatter(actuals, predictions, alpha=0.5, color='blue')
    axes[0].plot([min(actuals), max(actuals)], [min(actuals), max(actuals)], 'r--')
    axes[0].set_title('Predicted vs Actual Demand (LSTM)')
    axes[0].set_xlabel('Actual Demand (Units)')
    axes[0].set_ylabel('Predicted Demand (Units)')
    
    # Plot 2: Demand Over Time for one product
    sample_actuals = actuals[:50]
    sample_preds = predictions[:50]
    axes[1].plot(sample_actuals, label='Actual Demand', color='black', marker='o', markersize=4)
    axes[1].plot(sample_preds, label='LSTM Prediction', color='blue', linestyle='--')
    axes[1].fill_between(range(len(sample_preds)), 
                         np.array(sample_preds) - np.array(uncertainties[:50]), 
                         np.array(sample_preds) + np.array(uncertainties[:50]), 
                         color='blue', alpha=0.2, label='Confidence Interval (±σ)')
    axes[1].set_title('Time-Series Forecasting Sample')
    axes[1].set_xlabel('Time Steps (Days)')
    axes[1].set_ylabel('Demand (Units)')
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig('exports/lstm_evaluation.png', dpi=300)
    print("\n✅ Saved Graph: ai_service/exports/lstm_evaluation.png")

if __name__ == "__main__":
    evaluate_demand_model()
