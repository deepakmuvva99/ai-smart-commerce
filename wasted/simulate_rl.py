import pandas as pd
import numpy as np
import torch
import matplotlib.pyplot as plt
import seaborn as sns
import random
import os
import json

from models.demand_model import DemandForecastingModel
from models.sac_agent import SACAgent

def simulate_environment():
    print("Simulating Environment: SAC Pricing vs Static Baseline...")
    os.makedirs('exports', exist_ok=True)
    
    # 1. Initialize Models
    sac_agent = SACAgent(state_dim=6, action_dim=1, hidden_dim=128)
    # We will simulate learning from scratch to show the convergence over time
    
    model = DemandForecastingModel(input_dim=4, hidden_dim=64, num_layers=2)
    model.load_state_dict(torch.load('exports/demand_model.pt', map_location='cpu'))
    model.eval()
    
    # 2. Setup Simulation Parameters
    NUM_PRODUCTS = 5
    STEPS = 500 # Simulating 500 pricing cycles (e.g., 500 hours or days)
    
    # Initialize product states
    products = []
    for i in range(NUM_PRODUCTS):
        base_price = random.uniform(50, 500)
        cost_price = base_price * 0.4
        products.append({
            'id': i,
            'base_price': base_price,
            'cost_price': cost_price,
            'inventory': 1000,
            'sac_current_price': base_price,
            'sac_total_revenue': 0,
            'static_total_revenue': 0,
            'sac_total_profit': 0,
            'static_total_profit': 0,
            'traffic_history': [random.randint(5, 50) for _ in range(7)],
            'price_history': [base_price for _ in range(7)],
            'last_state': None,
            'last_action': None
        })
        
    metrics = {
        'step': [],
        'sac_cumulative_revenue': [],
        'static_cumulative_revenue': [],
        'actor_loss': [],
        'critic_loss': []
    }
    
    sac_cum_rev = 0
    static_cum_rev = 0
    
    # 3. Run Simulation Loop
    for step in range(STEPS):
        actor_loss, critic_loss = 0, 0
        
        for p in products:
            # Generate simulated traffic (random walk)
            traffic = max(1, p['traffic_history'][-1] + random.randint(-5, 5))
            p['traffic_history'].append(traffic)
            p['traffic_history'].pop(0) # Keep 7 days
            
            # Predict Base Demand using LSTM (using base price to estimate unbiased demand)
            day_of_week = step % 7
            seq = [[p['base_price'], p['price_history'][i], day_of_week, p['traffic_history'][i]] for i in range(7)]
            x_tensor = torch.tensor([seq], dtype=torch.float32)
            with torch.no_grad():
                mu, _, _ = model(x_tensor)
                base_demand = max(1, mu.item())
                
            # --- STATIC PRICING (Baseline) ---
            static_price = p['base_price']
            # Price Elasticity Formula: sales = base_demand * (base_price / actual_price)^1.5
            static_sales = max(0, int(base_demand * ((p['base_price'] / static_price) ** 1.5)))
            # Add some randomness to sales
            static_sales = max(0, static_sales + random.randint(-2, 2))
            static_rev = static_sales * static_price
            static_prof = static_rev - (static_sales * p['cost_price'])
            
            p['static_total_revenue'] += static_rev
            p['static_total_profit'] += static_prof
            static_cum_rev += static_rev
            
            # --- SAC RL PRICING ---
            state = [
                p['sac_current_price'] / 500.0,
                p['base_price'] / 500.0,
                p['inventory'] / 1000.0,
                traffic / 100.0,
                0, # Current sales (0 before action)
                base_demand / 100.0
            ]
            
            # Reward feedback from PREVIOUS step
            if p['last_state'] is not None:
                # Reward is profit generated in the last step
                reward = (p['last_sales'] * p['sac_current_price']) - (p['last_sales'] * p['cost_price'])
                if p['last_sales'] == 0:
                    reward = -10.0 # Penalty for no sales
                    
                sac_agent.store_transition(
                    state=p['last_state'],
                    action=p['last_action'],
                    reward=reward,
                    next_state=state,
                    done=False
                )
                
            # Get New Price from SAC
            evaluate = step > 400 # Exploit late in the simulation
            action = sac_agent.select_action(state, evaluate=evaluate)
            sac_price = max(p['cost_price'] * 1.05, min(p['base_price'] * action, p['base_price'] * 2.0))
            p['sac_current_price'] = sac_price
            
            # Calculate Actual Sales based on SAC price
            sac_sales = max(0, int(base_demand * ((p['base_price'] / sac_price) ** 1.5)))
            sac_sales = max(0, sac_sales + random.randint(-2, 2))
            sac_rev = sac_sales * sac_price
            sac_prof = sac_rev - (sac_sales * p['cost_price'])
            
            p['sac_total_revenue'] += sac_rev
            p['sac_total_profit'] += sac_prof
            sac_cum_rev += sac_rev
            
            # Update history and state tracking
            p['price_history'].append(sac_price)
            p['price_history'].pop(0)
            p['last_state'] = state
            p['last_action'] = action
            p['last_sales'] = sac_sales
            p['inventory'] = max(0, p['inventory'] - sac_sales)
            
            # Train SAC Agent
            if len(sac_agent.replay_buffer) > 64:
                update_info = sac_agent.update(batch_size=64)
                if update_info:
                    actor_loss = update_info['actor_loss']
                    critic_loss = update_info['critic_loss']
                    
        # Record metrics
        metrics['step'].append(step)
        metrics['sac_cumulative_revenue'].append(sac_cum_rev)
        metrics['static_cumulative_revenue'].append(static_cum_rev)
        metrics['actor_loss'].append(actor_loss)
        metrics['critic_loss'].append(critic_loss)
        
        if step % 50 == 0:
            print(f"Step {step}/{STEPS} | SAC Rev: ₹{sac_cum_rev * 80:.2f} | Static Rev: ₹{static_cum_rev * 80:.2f}")

    # Generate Performance Summary
    improvement = ((sac_cum_rev - static_cum_rev) / static_cum_rev) * 100
    
    # Scale to INR
    sac_cum_rev_inr = sac_cum_rev * 80
    static_cum_rev_inr = static_cum_rev * 80

    print("\n" + "="*50)
    print("💰 REINFORCEMENT LEARNING PRICING RESULTS")
    print("="*50)
    print(f"Total Cycles Simulated: {STEPS}")
    print(f"Static Pricing Revenue:  ₹{static_cum_rev_inr:,.2f}")
    print(f"SAC RL AI Revenue:       ₹{sac_cum_rev_inr:,.2f}")
    print(f"AI Revenue Uplift:       +{improvement:.2f}%")
    
    # 4. Generate Graphs
    sns.set_theme(style="whitegrid")
    
    # Scale the metrics lists to INR for the plots
    sac_cum_rev_list_inr = [x * 80 for x in metrics['sac_cumulative_revenue']]
    static_cum_rev_list_inr = [x * 80 for x in metrics['static_cumulative_revenue']]
    
    # Figure 1: Cumulative Revenue Comparison
    plt.figure(figsize=(10, 6))
    plt.plot(metrics['step'], sac_cum_rev_list_inr, label='SAC RL Pricing Strategy', color='green', linewidth=2.5)
    plt.plot(metrics['step'], static_cum_rev_list_inr, label='Static Baseline Pricing', color='gray', linestyle='--', linewidth=2)
    plt.fill_between(metrics['step'], static_cum_rev_list_inr, sac_cum_rev_list_inr, color='green', alpha=0.1)
    
    plt.title('Cumulative Revenue: AI Pricing vs Static Baseline', fontsize=14, pad=15)
    plt.xlabel('Simulation Steps (Time)', fontsize=12)
    plt.ylabel('Cumulative Revenue (₹)', fontsize=12)
    plt.legend(loc='upper left', fontsize=11)
    plt.tight_layout()
    plt.savefig('exports/rl_revenue_comparison.png', dpi=300)
    
    # Figure 2: SAC Agent Convergence (Training Loss)
    plt.figure(figsize=(10, 6))
    plt.plot(metrics['step'], metrics['critic_loss'], label='Critic (Value) Error', color='red', alpha=0.6)
    plt.plot(metrics['step'], metrics['actor_loss'], label='Actor (Policy) Loss', color='blue', alpha=0.6)
    plt.title('SAC Reinforcement Learning Convergence Curve', fontsize=14, pad=15)
    plt.xlabel('Training Steps', fontsize=12)
    plt.ylabel('Loss', fontsize=12)
    plt.yscale('symlog') # Handle negative values if any
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig('exports/rl_training_convergence.png', dpi=300)
    
    print("\n✅ Saved Graph: ai_service/exports/rl_revenue_comparison.png")
    print("✅ Saved Graph: ai_service/exports/rl_training_convergence.png")

if __name__ == "__main__":
    simulate_environment()
