"""Skill Headers and Job Types API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import SkillHeader, JobType, UserSkill
from app.schemas import (
    SkillHeaderResponse, UserSkillCreate, UserSkillResponse
)
from app.auth import get_current_user

router = APIRouter(prefix="/api", tags=["Skills"])


@router.get("/headers", response_model=List[SkillHeaderResponse])
async def get_skill_headers(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all skill headers with their job types"""
    headers = db.query(SkillHeader).filter(
        SkillHeader.is_active == True
    ).order_by(SkillHeader.display_order).all()
    
    response = []
    for header in headers:
        job_types = db.query(JobType).filter(
            JobType.header_id == header.header_id,
            JobType.is_active == True
        ).all()
        
        header_data = {
            "header_id": header.header_id,
            "name": header.name,
            "description": header.description,
            "question_depth": header.question_depth,
            "icon_url": header.icon_url,
            "job_types": [
                {
                    "job_type_id": jt.job_type_id,
                    "name": jt.name,
                    "description": jt.description,
                    "avg_simulation_minutes": jt.avg_simulation_minutes,
                    "submission_type": jt.submission_type
                }
                for jt in job_types
            ]
        }
        response.append(header_data)
    
    return response


@router.post("/user/skills", response_model=List[UserSkillResponse], status_code=status.HTTP_201_CREATED)
async def add_user_skills(
    skill_data: UserSkillCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Add job types to user's skills"""
    created_skills = []
    
    for job_type_id in skill_data.job_type_ids:
        # Check if job type exists
        job_type = db.query(JobType).filter(JobType.job_type_id == job_type_id).first()
        if not job_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job type {job_type_id} not found"
            )
        
        # Check if user already has this skill
        existing = db.query(UserSkill).filter(
            UserSkill.user_id == current_user.user_id,
            UserSkill.job_type_id == job_type_id
        ).first()
        
        if existing:
            continue  # Skip if already exists
        
        # Create user skill
        user_skill = UserSkill(
            user_id=current_user.user_id,
            job_type_id=job_type_id,
            current_rank="beginner",
            status="pending_simulation",
            total_attempts=0,
            passed_attempts=0
        )
        
        db.add(user_skill)
        db.commit()
        db.refresh(user_skill)
        
        created_skills.append({
            "id": user_skill.id,
            "job_type_id": user_skill.job_type_id,
            "job_type_name": job_type.name,
            "current_rank": user_skill.current_rank,
            "status": user_skill.status,
            "next_retake_available_at": user_skill.next_retake_available_at,
            "total_attempts": user_skill.total_attempts
        })
    
    return created_skills


@router.get("/user/skills", response_model=List[UserSkillResponse])
async def get_user_skills(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get current user's skills"""
    user_skills = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.user_id
    ).all()
    
    response = []
    for us in user_skills:
        job_type = db.query(JobType).filter(JobType.job_type_id == us.job_type_id).first()
        response.append({
            "id": us.id,
            "job_type_id": us.job_type_id,
            "job_type_name": job_type.name if job_type else "Unknown",
            "current_rank": us.current_rank,
            "status": us.status,
            "next_retake_available_at": us.next_retake_available_at,
            "total_attempts": us.total_attempts
        })
    
    return response
