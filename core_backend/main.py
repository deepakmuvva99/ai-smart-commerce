import os
import time
import logging
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from . import models
from .database import engine

import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "env": os.getenv("ENV", "development")
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

# Configure robust security logging
handler = logging.StreamHandler()
if os.getenv("ENV", "development").lower() == "production":
    handler.setFormatter(JSONFormatter())
else:
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))

logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger("api.security")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Commerce API Gateway")

if os.getenv("ENFORCE_HTTPS", "False").lower() == "true":
    app.add_middleware(HTTPSRedirectMiddleware)
    logger.info("HTTPS Strict Enforcement Enabled")

origins = [
    "http://localhost",
    "http://localhost:5173", # Vite default
    "http://127.0.0.1:5173", # Vite localhost alternative
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(f"[{client_ip}] {request.method} {request.url.path} - Status: {response.status_code} ({process_time:.2f}ms)")
        return response
    except Exception as exc:
        logger.error(f"[{client_ip}] {request.method} {request.url.path} - ALARM: Unhandled Server Exception - {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

from .routers import user, product, order, analytics
app.include_router(user.router)
app.include_router(product.router)
app.include_router(order.router)
app.include_router(analytics.router)

from . import scheduler
import httpx

@app.on_event("startup")
def startup_event():
    scheduler.start_scheduler()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown_scheduler()

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Commerce API Gateway"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# ============================================================
# Admin Control Endpoints
# ============================================================

from .routers.user import get_current_admin_user
from fastapi import Depends
from . import models

@app.get("/admin/status")
def admin_status(current_user: models.User = Depends(get_current_admin_user)):
    """Get the current status of the AI engine and scheduler."""
    running = scheduler.scheduler.running if hasattr(scheduler.scheduler, 'running') else False
    jobs = scheduler.scheduler.get_jobs() if running else []
    
    # Get AI service health
    ai_health = {}
    try:
        ai_url = os.environ.get("AI_SERVICE_URL", "http://ai_engine:8001")
        r = httpx.get(f"{ai_url}/health", timeout=2.0)
        ai_health = r.json()
    except:
        ai_health = {"status": "offline"}
    
    interval_seconds = 60
    if jobs:
        trigger = jobs[0].trigger
        if hasattr(trigger, 'interval'):
            interval_seconds = int(trigger.interval.total_seconds())

    return {
        "scheduler_running": running,
        "ai_service": ai_health,
        "interval_seconds": interval_seconds,
        "job_count": len(jobs),
    }

@app.post("/admin/toggle-scheduler")
def toggle_scheduler(enable: bool = True, current_user: models.User = Depends(get_current_admin_user)):
    """Turn the AI pricing scheduler on or off."""
    if enable:
        if not scheduler.scheduler.running:
            scheduler.start_scheduler()
        return {"status": "started", "message": "AI Pricing Scheduler activated."}
    else:
        if scheduler.scheduler.running:
            scheduler.scheduler.pause()
        return {"status": "paused", "message": "AI Pricing Scheduler paused."}

@app.post("/admin/resume-scheduler")
def resume_scheduler(current_user: models.User = Depends(get_current_admin_user)):
    """Resume a paused scheduler."""
    scheduler.scheduler.resume()
    return {"status": "resumed"}

@app.post("/admin/set-interval")
def set_interval(seconds: int = 60, current_user: models.User = Depends(get_current_admin_user)):
    """Change the scheduler run interval."""
    scheduler.scheduler.remove_all_jobs()
    scheduler.scheduler.add_job(
        scheduler.background_pricing_job, 'interval', 
        seconds=seconds, id='ai_pricing_optimizer_job', replace_existing=True
    )
    return {"status": "updated", "interval_seconds": seconds}

@app.post("/admin/retrain")
def trigger_retrain(current_user: models.User = Depends(get_current_admin_user)):
    """Forward retrain request to AI service."""
    try:
        ai_url = os.environ.get("AI_SERVICE_URL", "http://ai_engine:8001")
        r = httpx.post(f"{ai_url}/retrain", timeout=5.0)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@app.post("/admin/purge-db")
def purge_database(current_user: models.User = Depends(get_current_admin_user)):
    """Clear all traffic logs, orders, and price history. Products are kept."""
    from .database import SessionLocal
    db = SessionLocal()
    try:
        db.query(models.TrafficLog).delete()
        db.query(models.PriceHistory).delete()
        db.query(models.Order).delete()
        db.query(models.AIMetric).delete()
        # Reset all product prices back to base
        products = db.query(models.Product).all()
        for p in products:
            p.current_price = p.base_price
        db.commit()
        return {"status": "purged", "message": "All traffic, orders, and price history cleared. Prices reset to base."}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

