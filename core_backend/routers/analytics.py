from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from .. import models
from ..database import get_db

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)

from .user import get_current_admin_user

@router.get("/dashboard")
def get_dashboard_metrics(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin_user)):
    fifteen_mins_ago = datetime.utcnow() - timedelta(minutes=15)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Active users (product clicks in last 15 min)
    recent_traffic = db.query(models.TrafficLog).filter(models.TrafficLog.timestamp >= fifteen_mins_ago).count()
    
    # Traffic spikes (total clicks today)
    daily_traffic = db.query(models.TrafficLog).filter(models.TrafficLog.timestamp >= today_start).count()
    
    # AI Adjustments
    ai_adjustments = db.query(models.PriceHistory).count()
    
    # Revenue (Real from DB)
    real_revenue = db.query(func.sum(models.Order.total_amount)).scalar() or 0.0
    
    # Baseline Revenue (If sold at base price)
    baseline_result = db.query(func.sum(models.OrderItem.quantity * models.Product.base_price))\
        .join(models.ProductVariant, models.OrderItem.variant_id == models.ProductVariant.id)\
        .join(models.Product, models.ProductVariant.product_id == models.Product.id).scalar() or 0.0
        
    avg_price_result = db.query(func.avg(models.Product.current_price)).scalar() or 0.0

    return {
        "metrics": {
            "revenue": float(real_revenue),
            "baseline": float(baseline_result),
            "activeUsers": recent_traffic,
            "trafficSpikes": daily_traffic,
            "aiAdjustments": ai_adjustments
        },
        "timeseries": {
            "time": datetime.now().strftime('%I:%M %p'),
            "traffic": recent_traffic,
            "avg_price": float(avg_price_result),
            "revenue": float(real_revenue),
            "ai_predicted_baseline": float(baseline_result)
        }
    }
