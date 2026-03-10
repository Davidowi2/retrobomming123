"""Authentication API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

from app.database import get_db
from app.models import User, OTPVerification
from app.schemas import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    OTPRequest, OTPVerify, ErrorResponse
)
from app.auth import (
    get_password_hash, verify_password, create_access_token,
    create_refresh_token, get_current_user
)
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()


def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))


def send_otp_sms(phone: str, otp: str) -> bool:
    """Send OTP via SMS (mock implementation - integrate with SMS provider)"""
    # TODO: Integrate with Twilio, Africa's Talking, or local SMS provider
    print(f"[SMS TO {phone}] Your Crestal verification code: {otp}")
    return True


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if email exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if phone exists
    existing_phone = db.query(User).filter(User.phone == user_data.phone).first()
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        phone=user_data.phone,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        country=user_data.country,
        state=user_data.state,
        city=user_data.city,
        is_phone_verified=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate and send OTP
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    
    otp_record = OTPVerification(
        phone=user_data.phone,
        otp_code=otp_code,
        expires_at=expires_at
    )
    db.add(otp_record)
    db.commit()
    
    # Send SMS (async in production)
    send_otp_sms(user_data.phone, otp_code)
    
    # Create tokens
    token_data = {"sub": str(new_user.user_id), "email": new_user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(new_user)
    )


@router.post("/verify-otp", response_model=dict)
async def verify_otp(otp_data: OTPVerify, db: Session = Depends(get_db)):
    """Verify OTP code"""
    # Find latest OTP for phone
    otp_record = db.query(OTPVerification).filter(
        OTPVerification.phone == otp_data.phone,
        OTPVerification.verified_at.is_(None)
    ).order_by(OTPVerification.created_at.desc()).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP found for this phone number"
        )
    
    if otp_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired"
        )
    
    if otp_record.otp_code != otp_data.otp:
        otp_record.attempt_count += 1
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code"
        )
    
    # Mark OTP as verified
    otp_record.verified_at = datetime.utcnow()
    
    # Update user phone verification status
    user = db.query(User).filter(User.phone == otp_data.phone).first()
    if user:
        user.is_phone_verified = True
    
    db.commit()
    
    return {
        "message": "Phone verified successfully",
        "verified": True
    }


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    if login_data.device_fingerprint:
        user.device_fingerprint = login_data.device_fingerprint
    
    db.commit()
    
    # Create tokens
    token_data = {"sub": str(user.user_id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=dict)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token"""
    from app.auth import decode_token
    
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    token_data = {"sub": str(user.user_id), "email": user.email}
    new_access_token = create_access_token(token_data)
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse.model_validate(current_user)
