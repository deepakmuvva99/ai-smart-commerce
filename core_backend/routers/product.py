from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from .user import get_current_admin_user

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.ProductResponse])
def read_products(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), db: Session = Depends(get_db)):
    products = db.query(models.Product).filter(models.Product.is_active == True).offset(skip).limit(limit).all()
    return products

@router.post("/", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin_user)):
    product_data = product.dict(exclude={"variants"})
    db_product = models.Product(**product_data)
    
    for variant in product.variants:
        db_variant = models.ProductVariant(**variant.dict())
        db_product.variants.append(db_variant)
        
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/{product_id}", response_model=schemas.ProductResponse)
def read_product(product_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.put("/{product_id}", response_model=schemas.ProductResponse)
def update_product(product_id: int = Path(..., gt=0), product: schemas.ProductCreate = Depends(), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin_user)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
        
    product_data = product.dict(exclude={"variants"})
    for var, value in product_data.items():
        setattr(db_product, var, value) if value is not None else None
        
    if product.variants:
        db.query(models.ProductVariant).filter(models.ProductVariant.product_id == product_id).delete()
        for variant in product.variants:
            db_variant = models.ProductVariant(**variant.dict())
            db_product.variants.append(db_variant)
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/{product_id}")
def delete_product(product_id: int = Path(..., gt=0), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin_user)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Soft delete
    db_product.is_active = False
    db.add(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}

@router.post("/{product_id}/traffic")
def log_traffic(product_id: int = Path(..., gt=0), traffic_info: schemas.TrafficLogCreate = Depends(), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin_user)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
        
    db_traffic = models.TrafficLog(
        product_id=product_id,
        event_type=traffic_info.event_type
    )
    db.add(db_traffic)
    db.commit()
    return {"message": "Traffic logged successfully"}
