from fastapi import APIRouter, Depends, HTTPException, status, Request, Path
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Dict
from pydantic import BaseModel, EmailStr, Field
from .. import models, schemas, auth
from ..database import get_db
from jose import JWTError, jwt
import time
import logging
from collections import defaultdict

logger = logging.getLogger("api.security")

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

# In-memory rate limiting dictionary: ip -> list of timestamps
login_attempts = defaultdict(list)

def check_rate_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    # Keep only attempts from the last 60 seconds
    login_attempts[ip] = [t for t in login_attempts[ip] if now - t < 60]
    if len(login_attempts[ip]) >= 5:
        logger.warning(f"SECURITY ALARM: Brute force login threshold triggered for IP {ip}!")
        raise HTTPException(status_code=429, detail="Too many login attempts. Please try again in a minute.")
    login_attempts[ip].append(now)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_admin_user(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user

@router.post("/register")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    verification_token = auth.create_verification_token(user.email)
    
    db_user = models.User(
        email=user.email, 
        password_hash=hashed_password,
        verification_token=verification_token,
        is_verified=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # In a real app, this token would be emailed. For demo purposes, we return it.
    return {
        "user": schemas.UserResponse.from_orm(db_user),
        "message": "Registration successful. Please verify your email.",
        "verification_token": verification_token
    }

@router.get("/verify/{token}")
def verify_email(token: str = Path(..., min_length=10, max_length=250), db: Session = Depends(get_db)):
    email = auth.verify_token(token, "verification")
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
        
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or user.verification_token != token:
        raise HTTPException(status_code=400, detail="Invalid verification token")
        
    user.is_verified = True
    user.verification_token = None
    db.commit()
    return {"message": "Email verified successfully"}

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Apply rate limiting
    check_rate_limit(request)
    
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user:
        logger.warning(f"Login failed: Username {form_data.username} not found. Origin IP: {request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not auth.verify_password(form_data.password, user.password_hash):
        logger.warning(f"Login failed: Incorrect password for user {form_data.username}. Origin IP: {request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_verified:
        logger.warning(f"Login blocked: Unverified email {form_data.username} attempted login.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email before logging in.",
        )
        
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    logger.info(f"Login successful for user {form_data.username}.")
    return {"access_token": access_token, "token_type": "bearer"}

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user:
        # Don't leak whether an email is registered
        return {"message": "If that email is registered, a password reset link has been sent."}
        
    reset_token = auth.create_password_reset_token(user.email)
    user.reset_password_token = reset_token
    user.reset_password_expires = datetime.utcnow() + timedelta(minutes=auth.RESET_TOKEN_EXPIRE_MINUTES)
    db.commit()
    
    # In a real app, this token would be emailed. For demo purposes, we return it.
    return {
        "message": "If that email is registered, a password reset link has been sent.",
        "dev_reset_token": reset_token
    }

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=250)
    new_password: str = Field(..., min_length=8, max_length=128)

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = auth.verify_token(req.token, "reset")
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or user.reset_password_token != req.token:
        raise HTTPException(status_code=400, detail="Invalid reset token")
        
    if user.reset_password_expires and user.reset_password_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token has expired")
        
    user.password_hash = auth.get_password_hash(req.new_password)
    user.reset_password_token = None
    user.reset_password_expires = None
    db.commit()
    
    return {"message": "Password has been reset successfully"}

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user
