import random
from sqlalchemy.orm import Session
from .database import engine, get_db
from . import models

# Sample words to create realistic AI/Tech product names
categories = {
    "Earbuds": ["https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500&q=80", "https://images.unsplash.com/photo-1606220838315-056192d5e927?w=500&q=80", "https://images.unsplash.com/photo-1572569533944-411a052ff39f?w=500&q=80"],
    "Headphones": ["https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80", "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=500&q=80", "https://images.unsplash.com/photo-1599839619722-39751411ea63?w=500&q=80"],
    "Watch": ["https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&q=80", "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=500&q=80", "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=500&q=80"],
    "Keyboard": ["https://images.unsplash.com/photo-1595225476474-87563907a212?w=500&q=80", "https://images.unsplash.com/photo-1601445638532-3c6f6c3aa1d6?w=500&q=80", "https://images.unsplash.com/photo-1511467687858-23d386414ce6?w=500&q=80"],
    "Mouse": ["https://images.unsplash.com/photo-1527864550417-7fd11b445e52?w=500&q=80", "https://images.unsplash.com/photo-1615663245857-ac9310d79fe4?w=500&q=80"],
    "Router": ["https://images.unsplash.com/photo-1544154807-ca904323e0ec?w=500&q=80"],
    "Hub": ["https://images.unsplash.com/photo-1593640408182-31c70c8268f5?w=500&q=80"],
    "Monitor": ["https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500&q=80", "https://images.unsplash.com/photo-1616763355548-1b606f439fce?w=500&q=80"],
    "Camera": ["https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500&q=80", "https://images.unsplash.com/photo-1502920917128-1add50b4eace?w=500&q=80"],
    "Microphone": ["https://images.unsplash.com/photo-1598550476439-6847785fcea6?w=500&q=80"],
    "Speaker": ["https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=500&q=80", "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=500&q=80"],
    "Gamepad": ["https://images.unsplash.com/photo-1600080972464-8e5f35f63d08?w=500&q=80", "https://images.unsplash.com/photo-1563298723-dcfebaa392e3?w=500&q=80"]
}

descriptors = ["Neural", "Quantum", "Pulse", "Aero", "Hyper", "Neo", "Omni", "Core", "Vanguard", "Zero", "Apex", "Edge", "Sync", "Echo", "Lumina"]
suffixes = ["Pro", "X", "Max", "Elite", "Ultra", "Lite", "Plus", "V2", "Edition", "Studio"]

descriptions = [
    "AI-enhanced noise cancellation with deep learning adaptive EQ.",
    "Integrated biometric tracking tailored for high-performance athletes.",
    "Ultra-low latency mechanical switches designed for competitive esports.",
    "Spatial audio algorithms that map room acoustics in real time.",
    "Quantum-dot display technology offering unprecedented color gamut.",
    "Seamless mesh routing utilizing predictive traffic shaping.",
    "Ergonomic design crafted from aerospace-grade aluminum.",
    "Next-generation optics with AI-powered autofocus and tracking."
]

def generate_products(db: Session, count=100):
    print("Clearing existing products to re-seed with realistic images...")
    db.query(models.PriceHistory).delete()
    db.query(models.TrafficLog).delete()
    db.query(models.Order).delete()
    db.query(models.Product).delete()
    db.commit()

    print(f"Generating {count} products...")
    for _ in range(count):
        cat_name = random.choice(list(categories.keys()))
        name = f"{random.choice(descriptors)} {cat_name} {random.choice(suffixes)}"
        base_price = round(random.uniform(3999.00, 39999.00), 2)
        
        # 20% chance the current price is a discount
        if random.random() < 0.2:
            current_price = round(base_price * random.uniform(0.7, 0.95), 2)
        else:
            current_price = base_price
            
        cost_price = round(base_price * random.uniform(0.3, 0.6), 2)
        inventory = random.randint(5, 500)
        
        # Realistic category image
        image_url = random.choice(categories[cat_name])
        
        db_product = models.Product(
            name=name,
            description=random.choice(descriptions),
            base_price=base_price,
            current_price=current_price,
            cost_price=cost_price,
            inventory=inventory,
            image_url=image_url,
            is_active=True
        )
        db.add(db_product)
        
    db.commit()
    print("Database seeding completed.")

if __name__ == "__main__":
    db = next(get_db())
    generate_products(db, 110)
