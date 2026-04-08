from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from .user import get_current_user

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.OrderResponse)
def create_order(
    order: schemas.OrderCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    total_amount = 0.0
    db_order_items = []
    
    # Sort variants to avoid deadlocks when multiple users checkout simultaneously
    sorted_items = sorted(order.items, key=lambda x: x.variant_id)
    
    for item in sorted_items:
        # Transactional Row-Level Lock: Prevents other transactions from modifying this row until we commit
        variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == item.variant_id).with_for_update().first()
        
        if not variant:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Variant {item.variant_id} not found")
            
        if not variant.product.is_active:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Product for variant {item.variant_id} is inactive")
            
        if variant.inventory < item.quantity:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Not enough inventory for variant {item.variant_id}")
            
        # Deduct inventory atomically
        variant.inventory -= item.quantity
        db.add(variant)
        
        # Security: Re-calculate the price strictly on the backend, ignoring any frontend supplied total
        price_at_purchase = variant.product.current_price
        total_amount += price_at_purchase * item.quantity
        
        db_order_items.append(
            models.OrderItem(
                variant_id=item.variant_id,
                quantity=item.quantity,
                price_at_purchase=price_at_purchase
            )
        )
        
    db_order = models.Order(
        user_id=current_user.id,
        total_amount=total_amount,
        status="completed",
        items=db_order_items
    )
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    return db_order

@router.get("/me", response_model=List[schemas.OrderResponse])
def get_my_orders(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    orders = db.query(models.Order).filter(models.Order.user_id == current_user.id).all()
    return orders
