import sqlite3

conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=" * 60)
print("DATABASE: sql_app.db")
print("=" * 60)

for t in tables:
    tname = t[0]
    count = cursor.execute(f"SELECT COUNT(*) FROM [{tname}]").fetchone()[0]
    cols = [d[0] for d in cursor.execute(f"SELECT * FROM [{tname}] LIMIT 1").description]
    print(f"\nTABLE: {tname} ({count} rows)")
    print(f"  Columns: {cols}")

# Show sample products
print("\n" + "=" * 60)
print("SAMPLE PRODUCTS (first 5)")
print("=" * 60)
for row in cursor.execute("SELECT id, name, base_price, current_price, inventory FROM products LIMIT 5"):
    print(f"  ID:{row[0]} | {row[1]} | Base: ${row[2]:.2f} | AI Price: ${row[3]:.2f} | Stock: {row[4]}")

# Show orders
print("\n" + "=" * 60)
print("ALL ORDERS")
print("=" * 60)
for row in cursor.execute("SELECT id, product_id, quantity, price_at_purchase, created_at FROM orders"):
    print(f"  Order #{row[0]} | Product ID: {row[1]} | Qty: {row[2]} | Price: ${row[3]:.2f} | Date: {row[4]}")

order_count = cursor.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
if order_count == 0:
    print("  (No orders placed yet)")

# Show price history (AI adjustments)
print("\n" + "=" * 60)
print("RECENT AI PRICE ADJUSTMENTS (last 10)")
print("=" * 60)
for row in cursor.execute("SELECT ph.id, p.name, ph.old_price, ph.new_price, ph.reason, ph.timestamp FROM price_history ph JOIN products p ON ph.product_id = p.id ORDER BY ph.id DESC LIMIT 10"):
    print(f"  #{row[0]} | {row[1]} | ${row[2]:.2f} -> ${row[3]:.2f} | {row[4]} | {row[5]}")

ph_count = cursor.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
print(f"\n  Total AI price adjustments recorded: {ph_count}")

# Show traffic logs
print("\n" + "=" * 60)
print("TRAFFIC SUMMARY")
print("=" * 60)
traffic_count = cursor.execute("SELECT COUNT(*) FROM traffic_logs").fetchone()[0]
print(f"  Total traffic events (product views): {traffic_count}")

# Show top viewed products
print("\n  Top 5 Most Viewed Products:")
for row in cursor.execute("SELECT p.name, COUNT(t.id) as views FROM traffic_logs t JOIN products p ON t.product_id = p.id GROUP BY t.product_id ORDER BY views DESC LIMIT 5"):
    print(f"    {row[0]}: {row[1]} views")

conn.close()
