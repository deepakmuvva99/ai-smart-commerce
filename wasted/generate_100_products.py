from core_backend.database import SessionLocal
from core_backend import models
import random

def seed_100_db():
    db = SessionLocal()
    
    # Predefined Data for Procedural Generation
    categories = {
        "Tech & Electronics": {
            "images": [
                "https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&q=80&w=800",
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&q=80&w=800",
                "https://images.unsplash.com/photo-1523206489230-c012c64b2b48?auto=format&fit=crop&q=80&w=800",
                "https://images.unsplash.com/photo-1504274066651-8d31a536b11a?auto=format&fit=crop&q=80&w=800"
            ],
            "items": ["Wireless Earbuds", "Smart Watch Pro", "Gaming Mouse", "Mechanical Keyboard", "4K Monitor", "Noise Canceling Headphones", "Portable SSD 1TB", "Webcam 1080p", "Bluetooth Speaker", "Tablet Air", "Smartphone Ultra", "VR Headset", "Router Mesh", "Power Bank 20000mAh", "Streaming Microphone", "Drone 4K", "Action Camera", "E-Reader", "Smart Display", "Gaming Console Elite"]
        },
        "Apparel & Fashion": {
            "images": [
                "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&q=80&w=800",
                "https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&q=80&w=800",
                "https://images.unsplash.com/photo-1576566588028-4147f3842f27?auto=format&fit=crop&q=80&w=800",
                "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&q=80&w=800"
            ],
            "items": ["Classic Cotton T-Shirt", "Slim Fit Denim Jeans", "Vintage Leather Jacket", "Running Sneakers", "Athletic Hoodie", "Wool Blend Sweater", "Stretch Chino Pants", "Compression Shorts", "Puffer Vest", "Polo Shirt", "Cargo Pants", "Graphic Artist Tee", "Winter Parka Coat", "High-Waist Yoga Pants", "Suede Ankle Boots", "Silk Artisan Tie", "Moisture Wicking Socks", "Curved Baseball Cap", "Knit Beanie", "Polarized Sunglasses"]
        },
        "Home & Kitchen": {
            "images": [
                "https://images.unsplash.com/photo-1556910103-1c02745a8720?auto=format&fit=crop&q=80&w=800",
                "https://images.unsplash.com/photo-1584286595398-a59f21d313f5?auto=format&fit=crop&q=80&w=800",
                "https://images.unsplash.com/photo-1581622558667-3419a8dc5f83?auto=format&fit=crop&q=80&w=800",
                "https://images.unsplash.com/photo-1510915361894-fea3b1c820d1?auto=format&fit=crop&q=80&w=800"
            ],
            "items": ["Pour Over Coffee Maker", "Professional Blender", "Smart Air Fryer", "Digital Toaster Oven", "Damascus Knife Set", "Cast Iron Skillet Set", "Enameled Dutch Oven", "Artisan Stand Mixer", "12-Cup Food Processor", "Gooseneck Electric Kettle", "WiFi Smart Thermostat", "Self-Emptying Robot Vacuum", "HEPA Air Purifier", "Ultrasonic Essential Oil Diffuser", "Mulberry Silk Pillowcases", "Egyptian Cotton Sheets", "Weighted Throw Blanket", "Ceramic Decor Vases", "Minimalist Table Lamp", "Retro Wall Clock"]
        },
        "Sports & Fitness": {
            "images": [
                "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&q=80&w=800",
                "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?auto=format&fit=crop&q=80&w=800",
                "https://images.unsplash.com/photo-1540497077202-7c8a3999166f?auto=format&fit=crop&q=80&w=800",
                "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&q=80&w=800"
            ],
            "items": ["Non-Slip Yoga Mat", "Adjustable Dumbbell Set", "Heavy Resistance Bands", "Cast Iron Kettlebell 15lb", "Speed Jump Rope", "Deep Tissue Foam Roller", "Insulated Protein Shaker", "Duffel Gym Bag", "Compact Under-Desk Treadmill", "Magnetic Exercise Bike", "Water Resistance Rowing Machine", "Doorway Pull Up Bar", "Core Ab Wheel", "Percussion Massage Gun", "Adjustable Weight Bench", "Pro Boxing Gloves", "Stability Pilates Ball", "Aerobic Step Platform", "Adjustable Grip Strengthener", "Tactical Weighted Vest"]
        },
        "Beauty & Care": {
            "images": [
                "https://images.unsplash.com/photo-1596462502278-27bf85033e5a?auto=format&fit=crop&q=80&w=800",
                "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&q=80&w=800",
                "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&q=80&w=800",
                "https://images.unsplash.com/photo-1571781526291-c477eb66338e?auto=format&fit=crop&q=80&w=800"
            ],
            "items": ["Vitamin C Brightening Serum", "Daily Hydrating Moisturizer", "Mineral Sunscreen SPF 50", "Peptide Eye Cream", "Gentle Cleansing Oil", "Pore Refining Clay Mask", "Microdermabrasion Exfoliating Scrub", "Organic Rose Water Toner", "Overnight Lip Balm", "Shea Butter Body Lotion", "Argan Hair Serum", "Sulfate-Free Shampoo Set", "Vegan Nail Polish Collection", "Pro Makeup Brushes 12pc", "Liquid Foundation Matte", "Volumizing Mascara", "Signature Eau de Parfum", "Woodsy Men's Cologne", "Sandalwood Beard Oil", "Classic Wet Shaving Kit"]
        }
    }

    brand_prefixes = ["Aura", "Nova", "Zen", "Vortex", "Lumina", "Apex", "Prime", "Elite", "Core", "Optima", "Nexus", "Quantum"]
    
    products_to_insert = []
    
    for cat_name, details in categories.items():
        for item_name in details["items"]:
            # Construct a realistic name
            brand = random.choice(brand_prefixes)
            product_name = f"{brand} {item_name}"
            
            # Formulate realistic economics
            base_p = round(random.uniform(19.99, 199.99), 2)
            
            # Expensive keyword overrides
            expensive_triggers = ["Monitor", "Console", "Drone", "Treadmill", "Bike", "Robot", "Purifier"]
            if any(word in item_name for word in expensive_triggers):
                base_p = round(random.uniform(299.99, 999.99), 2)
                
            cost_p = round(base_p * random.uniform(0.3, 0.7), 2)
            
            # Select random image from this category pool
            img = random.choice(details["images"])
            
            # Define specific product variants based on the category
            variants = []
            if cat_name == "Apparel & Fashion":
                sizes = ["S", "M", "L", "XL"]
                colors = ["Black", "White", "Navy Blue", "Heather Gray"]
                # Add 3-5 random sizes/colors
                for s in random.sample(sizes, random.randint(2, 4)):
                    for c in random.sample(colors, random.randint(1, 2)):
                        variants.append({"size": s, "color": c, "inventory": random.randint(0, 45)})
            elif cat_name == "Tech & Electronics":
                colors = ["Space Gray", "Silver", "Matte Black", "Alpine White"]
                for c in random.sample(colors, random.randint(2, 4)):
                    variants.append({"size": "Standard", "color": c, "inventory": random.randint(5, 30)})
            else:
                variants.append({"size": "Standard Size", "color": "Original", "inventory": random.randint(10, 150)})

            products_to_insert.append({
                "name": product_name,
                "description": f"The new {product_name} delivers incredible value. Expertly crafted for the {cat_name} category to elevate your daily routine.",
                "base_price": base_p,
                "current_price": base_p,
                "cost_price": cost_p,
                "image_url": img,
                "variants": variants
            })

    print(f"Executing insertion of {len(products_to_insert)} procedurally generated products into SQLite Engine...")
    
    for p_data in products_to_insert:
        variants = p_data.pop("variants")
        db_product = models.Product(**p_data)
        for v in variants:
            db_product.variants.append(models.ProductVariant(**v))
        db.add(db_product)

    try:
        db.commit()
        print(f"DATABASE UPDATE SUCCESSFUL: Total {len(products_to_insert)} dynamic products loaded. AI Pricing AI pool expanded.")
    except Exception as e:
        print(f"Error executing bulk transaction: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_100_db()
