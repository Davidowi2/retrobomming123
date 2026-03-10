"""Pydantic Schemas for API Request/Response Validation"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID


# ============== USER SCHEMAS ==============

class UserCreate(BaseModel):
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+?[0-9]{10,15}$")
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    country: str = "Nigeria"
    state: Optional[str] = None
    city: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    device_fingerprint: Optional[str] = None


class UserResponse(BaseModel):
    user_id: UUID
    email: str
    phone: str
    full_name: str
    avatar_url: Optional[str]
    country: str
    state: Optional[str]
    role: str
    is_phone_verified: bool
    is_id_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============== OTP SCHEMAS ==============

class OTPRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+?[0-9]{10,15}$")


class OTPVerify(BaseModel):
    phone: str = Field(..., pattern=r"^\+?[0-9]{10,15}$")
    otp: str = Field(..., min_length=4, max_length=6)


# ============== SKILL HEADER SCHEMAS ==============

class JobTypeSummary(BaseModel):
    job_type_id: UUID
    name: str
    description: str
    avg_simulation_minutes: int
    submission_type: str
    
    class Config:
        from_attributes = True


class SkillHeaderResponse(BaseModel):
    header_id: UUID
    name: str
    description: str
    question_depth: str
    icon_url: Optional[str]
    job_types: List[JobTypeSummary]
    
    class Config:
        from_attributes = True


# ============== USER SKILL SCHEMAS ==============

class UserSkillCreate(BaseModel):
    job_type_ids: List[UUID]


class UserSkillResponse(BaseModel):
    id: UUID
    job_type_id: UUID
    job_type_name: str
    current_rank: str
    status: str
    next_retake_available_at: Optional[datetime]
    total_attempts: int
    
    class Config:
        from_attributes = True


# ============== SIMULATION SCHEMAS ==============

class SimulationStart(BaseModel):
    job_type_id: UUID
    level: str = Field(..., pattern=r"^(beginner|intermediate|advanced|expert)$")


class SimulationStartResponse(BaseModel):
    session_id: UUID
    job_type_name: str
    level: str
    total_questions: int
    estimated_minutes: int
    knowledge_section_percentage: int = 68
    mini_task_percentage: int = 32
    pass_threshold: float = 80.0
    cooldown_applies: bool
    first_question: Dict[str, Any]


class AnswerSubmit(BaseModel):
    question_id: UUID
    answer: str
    time_spent_seconds: int


class AnswerResponse(BaseModel):
    correct: bool
    next_question: Optional[Dict[str, Any]]
    section_complete: bool = False
    knowledge_score: Optional[float] = None
    next_section: Optional[str] = None
    mini_task: Optional[Dict[str, Any]] = None
    progress: Dict[str, int]


class MiniTaskSubmit(BaseModel):
    task_id: UUID
    submission_content: Optional[str] = None


class MiniTaskResponse(BaseModel):
    submission_id: UUID
    status: str
    estimated_seconds: int


class SimulationResults(BaseModel):
    session_id: UUID
    status: str
    overall_passed: bool
    scores: Dict[str, Any]
    rank: Dict[str, Any]
    skill_dna: Dict[str, Any]
    next_steps: Dict[str, Any]


# ============== SKILL DNA SCHEMAS ==============

class ConceptStrength(BaseModel):
    concept: str
    strength: float
    fail_count: int
    pass_count: int
    status: str


class SkillDNAResponse(BaseModel):
    job_type_id: UUID
    job_type_name: str
    current_rank: str
    overall_strength: float
    concept_breakdown: List[ConceptStrength]
    radar_chart_data: Dict[str, Any]
    recommended_focus: List[str]


# ============== COOLDOWN SCHEMAS ==============

class CooldownStatus(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    next_available_at: Optional[datetime] = None
    hours_remaining: Optional[float] = None
    attempt_number: Optional[int] = None


# ============== ERROR SCHEMAS ==============

class ErrorResponse(BaseModel):
    error: str
    details: Optional[List[str]] = None
    message: Optional[str] = None
