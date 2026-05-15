from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128, description="Password must be between 8 and 128 characters to prevent Bcrypt DoS.")

class UserResponse(UserBase):
    id: int
    role: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ProductVariantBase(BaseModel):
    size: Optional[str] = Field(None, max_length=50, pattern=r"^[\w\s\-]+$")
    color: Optional[str] = Field(None, max_length=50, pattern=r"^[\w\s\-]+$")
    inventory: int = Field(..., ge=0, description="Inventory cannot be negative")

class ProductVariantCreate(ProductVariantBase):
    pass

class ProductVariantResponse(ProductVariantBase):
    id: int
    product_id: int
    
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, pattern=r"^[\w\s\-\.\,\&]+$")
    description: Optional[str] = Field(None, max_length=2000)
    base_price: float = Field(..., gt=0.0)
    current_price: float = Field(..., gt=0.0)
    cost_price: float = Field(..., gt=0.0)
    image_url: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = True

class ProductCreate(ProductBase):
    variants: List[ProductVariantCreate] = []

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    inventory: int
    variants: List[ProductVariantResponse] = []

    class Config:
        from_attributes = True

class TrafficLogCreate(BaseModel):
    event_type: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-zA-Z0-9\_]+$")

class OrderItemCreate(BaseModel):
    variant_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=1000, description="Prevent logical injections using negative quantities.")

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class OrderItemResponse(BaseModel):
    id: int
    variant_id: int
    quantity: int
    price_at_purchase: float
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True
