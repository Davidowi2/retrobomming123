"""SQLAlchemy Models for Crestal"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, DECIMAL, JSON, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(36), primary_key=True, default=str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    avatar_url = Column(String(500))
    country = Column(String(100), nullable=False, default="Nigeria")
    state = Column(String(100))
    city = Column(String(100))
    role = Column(String(20), nullable=False, default="worker")
    is_phone_verified = Column(Boolean, default=False)
    is_id_verified = Column(Boolean, default=False)
    id_verified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    device_fingerprint = Column(String(255))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user_skills = relationship("UserSkill", back_populates="user")
    sessions = relationship("SimulationSession", back_populates="user")
    skill_dna = relationship("UserSkillDNA", back_populates="user")


class SkillHeader(Base):
    __tablename__ = "skill_headers"
    
    header_id = Column(String(36), primary_key=True, default=str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    question_depth = Column(String(20), nullable=False)
    icon_url = Column(String(500))
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job_types = relationship("JobType", back_populates="header")


class JobType(Base):
    __tablename__ = "job_types"
    
    job_type_id = Column(String(36), primary_key=True, default=str(uuid.uuid4()))
    header_id = Column(String(36), ForeignKey("skill_headers.header_id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    submission_type = Column(String(50), nullable=False)
    avg_simulation_minutes = Column(Integer, nullable=False)
    mini_task_rubric = Column(JSON, default={})
    question_count_beginner = Column(Integer, default=20)
    question_count_intermediate = Column(Integer, default=30)
    question_count_advanced = Column(Integer, default=40)
    question_count_expert = Column(Integer, default=50)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    header = relationship("SkillHeader", back_populates="job_types")
    user_skills = relationship("UserSkill", back_populates="job_type")
    sessions = relationship("SimulationSession", back_populates="job_type")
    concepts = relationship("ConceptPool", back_populates="job_type")


class UserSkill(Base):
    __tablename__ = "user_skills"
    
    id = Column(String(36), primary_key=True, default=str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    job_type_id = Column(String(36), ForeignKey("job_types.job_type_id"), nullable=False)
    current_rank = Column(String(20), nullable=False, default="beginner")
    rank_score = Column(DECIMAL(5, 2), default=0.00)
    status = Column(String(20), nullable=False, default="pending_simulation")
    last_simulation_at = Column(DateTime)
    next_retake_available_at = Column(DateTime)
    total_attempts = Column(Integer, default=0)
    passed_attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_skills")
    job_type = relationship("JobType", back_populates="user_skills")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'job_type_id', name='unique_user_job_type'),
    )


class SimulationSession(Base):
    __tablename__ = "simulation_sessions"
    
    session_id = Column(String(36), primary_key=True, default=str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    job_type_id = Column(String(36), ForeignKey("job_types.job_type_id"), nullable=False)
    level = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="in_progress")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    knowledge_score = Column(DECIMAL(5, 2))
    mini_task_score = Column(DECIMAL(5, 2))
    mini_task_passed = Column(Boolean)
    overall_passed = Column(Boolean)
    skill_dna_snapshot = Column(JSON)
    attempt_number = Column(Integer, default=1)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_token_hash = Column(String(255))
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    job_type = relationship("JobType", back_populates="sessions")
    questions = relationship("SimulationQuestion", back_populates="session")
    task_submission = relationship("TaskSubmission", back_populates="session", uselist=False)


class SimulationQuestion(Base):
    __tablename__ = "simulation_questions"
    
    question_id = Column(String(36), primary_key=True, default=str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("simulation_sessions.session_id"), nullable=False)
    concept_area = Column(String(100), nullable=False)
    question_type = Column(String(20), nullable=False)
    question_text = Column(Text, nullable=False)
    answer_options = Column(JSON, nullable=False)
    correct_answer = Column(String(500), nullable=False)
    worker_answer = Column(String(500))
    is_correct = Column(Boolean)
    order_index = Column(Integer, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime)
    time_spent_seconds = Column(Integer)
    
    # Relationships
    session = relationship("SimulationSession", back_populates="questions")


class TaskSubmission(Base):
    __tablename__ = "task_submissions"
    
    submission_id = Column(String(36), primary_key=True, default=str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("simulation_sessions.session_id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    job_type_id = Column(String(36), ForeignKey("job_types.job_type_id"), nullable=False)
    task_description = Column(Text, nullable=False)
    submission_content = Column(Text)
    file_url = Column(String(500))
    submitted_at = Column(DateTime, default=datetime.utcnow)
    auto_score = Column(DECIMAL(5, 2))
    ai_evaluation = Column(JSON)
    peer_review_score = Column(DECIMAL(5, 2))
    peer_reviewer_id = Column(String(36), ForeignKey("users.user_id"))
    passed = Column(Boolean)
    feedback_notes = Column(Text)
    evaluation_status = Column(String(20), default="pending")
    
    # Relationships
    session = relationship("SimulationSession", back_populates="task_submission")


class UserSkillDNA(Base):
    __tablename__ = "user_skill_dna"
    
    id = Column(String(36), primary_key=True, default=str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    job_type_id = Column(String(36), ForeignKey("job_types.job_type_id"), nullable=False)
    concept_area = Column(String(100), nullable=False)
    fail_count = Column(Integer, default=0)
    pass_count = Column(Integer, default=0)
    weakness_score = Column(DECIMAL(4, 3))
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="skill_dna")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'job_type_id', 'concept_area', name='unique_user_job_concept'),
    )


class CooldownTracking(Base):
    __tablename__ = "cooldown_tracking"
    
    id = Column(String(36), primary_key=True, default=str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    job_type_id = Column(String(36), ForeignKey("job_types.job_type_id"), nullable=False)
    level = Column(String(20), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    next_available_at = Column(DateTime, nullable=False)
    passed = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'job_type_id', 'level', 'attempt_number', name='unique_attempt'),
    )


class ConceptPool(Base):
    __tablename__ = "concept_pools"
    
    concept_id = Column(String(36), primary_key=True, default=str(uuid.uuid4()))
    job_type_id = Column(String(36), ForeignKey("job_types.job_type_id"), nullable=False)
    concept_key = Column(String(100), nullable=False)
    concept_name = Column(String(255), nullable=False)
    definition = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=False)
    question_templates = Column(JSON, default=[])
    nigerian_contexts = Column(JSON, default=[])
    common_mistakes = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job_type = relationship("JobType", back_populates="concepts")
    
    __table_args__ = (
        UniqueConstraint('job_type_id', 'concept_key', name='unique_job_concept'),
    )


class OTPVerification(Base):
    __tablename__ = "otp_verifications"
    
    id = Column(String(36), primary_key=True, default=str(uuid.uuid4()))
    phone = Column(String(20), nullable=False)
    otp_code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime)
    attempt_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
