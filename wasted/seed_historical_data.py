import sqlite3
import random
from datetime import datetime, timedelta
import os

def seed_history_fast(db_path, days=60):
    print(f"Connecting to {db_path} to seed {days} days of historical data...")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # We need products and their variants
    products = c.execute("SELECT p.id, p.current_price, v.id FROM products p JOIN product_variants v ON p.id = v.product_id GROUP BY p.id").fetchall()
    
    if not products:
        print("No products. Run a product seed script first.")
        return
        
    c.execute("INSERT OR IGNORE INTO users (id, email, password_hash, role) VALUES (9999, 'history@example.com', 'hash', 'user')")
    user_id = 9999
    
    # Determine the maximum order ID to prevent primary key conflicts
    max_order_id = c.execute("SELECT MAX(id) FROM orders").fetchone()
    order_id = (max_order_id[0] or 0) + 1
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    traffic_logs = []
    orders = []
    order_items = []
    
    for i in range(days):
        # We process one full day at a time
        current_date = start_date + timedelta(days=i)
        str_date = current_date.strftime("%Y-%m-%d 12:00:00")
        day_of_week = current_date.weekday()
        weekend_mult = 1.3 if day_of_week >= 5 else 1.0
        
        for p_id, price, v_id in products:
            base_demand = random.uniform(2, 8)
            traffic_views = int(base_demand * random.uniform(2, 5) * weekend_mult)
            
            for _ in range(traffic_views):
                traffic_logs.append((p_id, user_id, "view", str_date))
                
            expected_demand = base_demand * weekend_mult * random.uniform(0.8, 1.2)
            actual_demand = max(0, int(expected_demand))
            
            if actual_demand > 0:
                orders.append((order_id, user_id, price * actual_demand, "paid", str_date))
                order_items.append((order_id, v_id, actual_demand, price))
                order_id += 1
                
    c.executemany("INSERT INTO traffic_logs (product_id, user_id, event_type, timestamp) VALUES (?, ?, ?, ?)", traffic_logs)
    c.executemany("INSERT INTO orders (id, user_id, total_amount, status, created_at) VALUES (?, ?, ?, ?, ?)", orders)
    c.executemany("INSERT INTO order_items (order_id, variant_id, quantity, price_at_purchase) VALUES (?, ?, ?, ?)", order_items)
    conn.commit()
    
    conn.close()
    print(f"Successfully seeded {len(traffic_logs)} traffic logs and {len(orders)} orders over {days} days.")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'sql_app.db')
    seed_history_fast(db_path, days=60)
