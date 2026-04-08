from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="user") # admin/user
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True, index=True)
    reset_password_token = Column(String, nullable=True, index=True)
    reset_password_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    cart = relationship("Cart", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    base_price = Column(Float)
    current_price = Column(Float)
    cost_price = Column(Float)
    image_url = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

    @property
    def inventory(self):
        return sum(variant.inventory for variant in self.variants)

class ProductVariant(Base):
    __tablename__ = "product_variants"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    size = Column(String, nullable=True) # S, M, L, etc
    color = Column(String, nullable=True) # Red, Blue, etc
    inventory = Column(Integer, default=0)
    
    product = relationship("Product", back_populates="variants")

class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    user = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"))
    variant_id = Column(Integer, ForeignKey("product_variants.id"))
    quantity = Column(Integer, default=1)
    
    cart = relationship("Cart", back_populates="items")
    variant = relationship("ProductVariant")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float)
    status = Column(String, default="pending") # pending, paid, shipped, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    variant_id = Column(Integer, ForeignKey("product_variants.id"))
    quantity = Column(Integer)
    price_at_purchase = Column(Float)
    
    order = relationship("Order", back_populates="items")
    variant = relationship("ProductVariant")

class TrafficLog(Base):
    __tablename__ = "traffic_logs"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    old_price = Column(Float)
    new_price = Column(Float)
    demand_score = Column(Float)
    reason = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AIMetric(Base):
    __tablename__ = "ai_metrics"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    predicted_demand = Column(Float)
    uncertainty = Column(Float)
    reward = Column(Float)
    model_version = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
