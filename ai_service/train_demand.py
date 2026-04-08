import pandas as pd
import numpy as np
import torch
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import os
from models.demand_model import DemandForecastingModel, nll_loss

# Hyperparameters
SEQ_LEN = 7 # Look back 7 days
BATCH_SIZE = 16
EPOCHS = 100
LEARNING_RATE = 0.001

class DemandDataset(Dataset):
    def __init__(self, csv_file, seq_len=7):
        # Load and sort data
        self.df = pd.read_csv(csv_file)
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.df = self.df.sort_values(by=['Product_ID', 'Date'])
        self.seq_len = seq_len
        
        # Features: Base_Price, Current_Price, Day_Of_Week, Traffic_Views
        # Target: Demand_Units
        
        # Normalize features individually for better convergence
        self.features = ['Base_Price', 'Current_Price', 'Day_Of_Week', 'Traffic_Views']
        for col in self.features:
            self.df[col] = (self.df[col] - self.df[col].mean()) / (self.df[col].std() + 1e-8)
            
        self.samples = []
        
        # Create sequences per product
        for p_id in self.df['Product_ID'].unique():
            p_data = self.df[self.df['Product_ID'] == p_id].reset_index(drop=True)
            if len(p_data) <= self.seq_len:
                continue
                
            for i in range(len(p_data) - self.seq_len):
                # (seq_len, num_features)
                x = p_data.loc[i:i+self.seq_len-1, self.features].values
                # Target demand for the day *after* the sequence
                y = p_data.loc[i+self.seq_len, 'Demand_Units']
                
                self.samples.append((x, y))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        x, y = self.samples[idx]
        return torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)

def train_model():
    print("Loading dataset...")
    data_path = 'dataset/real_demand_data.csv'
    if not os.path.exists(data_path):
        print(f"Dataset not found at {data_path}. Run dataset/ingest_data.py first.")
        return
        
    dataset = DemandDataset(data_path, seq_len=SEQ_LEN)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    print(f"Total sequences generated: {len(dataset)}")
    
    # 4 input features
    model = DemandForecastingModel(input_dim=4, hidden_dim=64, num_layers=2)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    print("Starting training...")
    model.train()
    
    for epoch in range(1, EPOCHS + 1):
        epoch_loss = 0
        for batch_x, batch_y in dataloader:
            optimizer.zero_grad()
            
            # Forward pass
            mu, sigma, _ = model(batch_x)
            
            # Compute Negative Log-Likelihood Loss
            loss = nll_loss(mu.squeeze(), sigma.squeeze(), batch_y)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping to prevent exploding gradients in LSTMs
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            epoch_loss += loss.item()
            
        avg_loss = epoch_loss / len(dataloader)
        
        if epoch % 10 == 0 or epoch == 1:
            print(f"Epoch [{epoch}/{EPOCHS}] | Loss (NLL): {avg_loss:.4f}")

    # Export model artifact
    os.makedirs('exports', exist_ok=True)
    export_path = 'exports/demand_model.pt'
    torch.save(model.state_dict(), export_path)
    print(f"Training complete! Model saved to {export_path}")

if __name__ == "__main__":
    train_model()
