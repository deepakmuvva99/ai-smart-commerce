from core_backend.database import SessionLocal
from core_backend import models

def seed_db():
    db = SessionLocal()
    
    products = [
        {
            "name": "Sony WH-1000XM5 Headphones",
            "description": "Industry leading noise canceling with two processors and eight microphones.",
            "base_price": 348.00,
            "current_price": 348.00,
            "cost_price": 150.00,
            "image_url": "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?auto=format&fit=crop&q=80&w=800",
            "variants": [
                {"size": "One Size", "color": "Black", "inventory": 45},
                {"size": "One Size", "color": "Silver", "inventory": 12}
            ]
        },
        {
            "name": "Apple MacBook Pro M3",
            "description": "The most advanced Mac ever built, featuring the M3 Max chip.",
            "base_price": 2499.00,
            "current_price": 2499.00,
            "cost_price": 1800.00,
            "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&q=80&w=800",
            "variants": [
                {"size": "14-inch", "color": "Space Black", "inventory": 8},
                {"size": "16-inch", "color": "Silver", "inventory": 3}
            ]
        },
        {
            "name": "Samsung 49-inch Odyssey G9",
            "description": "Curved Gaming Monitor with 240Hz refresh rate.",
            "base_price": 1299.99,
            "current_price": 1299.99,
            "cost_price": 850.00,
            "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&q=80&w=800",
            "variants": [
                {"size": "49-inch", "color": "White", "inventory": 20}
            ]
        }
    ]

    for p_data in products:
        variants = p_data.pop("variants")
        db_product = models.Product(**p_data)
        for v in variants:
            db_product.variants.append(models.ProductVariant(**v))
        db.add(db_product)

    db.commit()
    db.close()
    print("Database seeded with Product Variants!")

if __name__ == "__main__":
    seed_db()
