"""Simulation API Endpoints - Core of Crestal Platform"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
import hashlib
import json
import random
import google.generativeai as genai

from app.database import get_db
from app.models import (
    SimulationSession, SimulationQuestion, TaskSubmission,
    UserSkill, JobType, ConceptPool, CooldownTracking, UserSkillDNA
)
from app.schemas import (
    SimulationStart, SimulationStartResponse, AnswerSubmit, AnswerResponse,
    MiniTaskSubmit, MiniTaskResponse, SimulationResults, CooldownStatus
)
from app.auth import get_current_user
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/simulations", tags=["Simulations"])

# Initialize Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.0-flash')


def get_cooldown_hours(level: str) -> int:
    """Get cooldown hours based on level"""
    cooldowns = {
        "beginner": settings.COOLDOWN_HOURS_BEGINNER,
        "intermediate": settings.COOLDOWN_HOURS_INTERMEDIATE,
        "advanced": settings.COOLDOWN_HOURS_ADVANCED,
        "expert": settings.COOLDOWN_HOURS_EXPERT
    }
    return cooldowns.get(level, 48)


def check_cooldown(db: Session, user_id, job_type_id: str, level: str) -> CooldownStatus:
    """Check if user can start simulation or is in cooldown"""
    # Get last completed attempt
    last_attempt = db.query(CooldownTracking).filter(
        CooldownTracking.user_id == user_id,
        CooldownTracking.job_type_id == job_type_id,
        CooldownTracking.level == level,
        CooldownTracking.completed_at.isnot(None)
    ).order_by(CooldownTracking.completed_at.desc()).first()
    
    if not last_attempt:
        return CooldownStatus(allowed=True)
    
    # If passed, can retake immediately for level-up
    if last_attempt.passed:
        return CooldownStatus(allowed=True, reason="LEVEL_UP_AVAILABLE")
    
    # Check cooldown
    cooldown_hours = get_cooldown_hours(level)
    next_available = last_attempt.completed_at + timedelta(hours=cooldown_hours)
    
    if datetime.utcnow() >= next_available:
        return CooldownStatus(allowed=True)
    
    hours_remaining = (next_available - datetime.utcnow()).total_seconds() / 3600
    
    return CooldownStatus(
        allowed=False,
        reason="COOLDOWN_ACTIVE",
        next_available_at=next_available,
        hours_remaining=round(hours_remaining, 1),
        attempt_number=last_attempt.attempt_number + 1
    )


def get_question_count(db: Session, job_type_id: str, level: str) -> int:
    """Get question count based on job type and level"""
    job_type = db.query(JobType).filter(JobType.job_type_id == job_type_id).first()
    if not job_type:
        return 25
    
    counts = {
        "beginner": job_type.question_count_beginner,
        "intermediate": job_type.question_count_intermediate,
        "advanced": job_type.question_count_advanced,
        "expert": job_type.question_count_expert
    }
    return counts.get(level, 25)


def select_concepts(db: Session, job_type_id: str, level: str, count: int, user_id=None) -> List[ConceptPool]:
    """Select concepts for simulation - balanced or weighted for retakes"""
    # Get all concepts for job type at or below this level
    available = db.query(ConceptPool).filter(
        ConceptPool.job_type_id == job_type_id,
        ConceptPool.is_active == True
    ).all()
    
    if not available:
        return []
    
    # Group by concept key
    concept_groups = {}
    for c in available:
        if c.concept_key not in concept_groups:
            concept_groups[c.concept_key] = []
        concept_groups[c.concept_key].append(c)
    
    selected = []
    
    # For retakes: check if user has weak areas
    if user_id:
        weak_areas = db.query(UserSkillDNA).filter(
            UserSkillDNA.user_id == user_id,
            UserSkillDNA.job_type_id == job_type_id,
            UserSkillDNA.weakness_score > 0.3
        ).order_by(UserSkillDNA.weakness_score.desc()).all()
        
        # 60% from weak areas
        weak_count = int(count * 0.6)
        for dna in weak_areas[:weak_count]:
            if dna.concept_area in concept_groups:
                selected.append(random.choice(concept_groups[dna.concept_area]))
    
    # Fill remaining with balanced selection
    remaining = count - len(selected)
    other_concepts = [c for c in available if c not in selected]
    
    for _ in range(remaining):
        if other_concepts:
            selected.append(random.choice(other_concepts))
        elif available:
            selected.append(random.choice(available))
    
    random.shuffle(selected)
    return selected[:count]


def generate_question_with_gemini(concept: ConceptPool, level: str, order_index: int) -> dict:
    """Generate a single question using Gemini API"""
    templates = concept.question_templates or []
    contexts = concept.nigerian_contexts or []
    mistakes = concept.common_mistakes or []
    
    if not templates or not contexts:
        return None
    
    template = random.choice(templates)
    context = random.choice(contexts)
    wrong_answers = random.sample(mistakes, min(3, len(mistakes))) if mistakes else ["Wrong A", "Wrong B", "Wrong C"]
    
    prompt = f"""You are creating a multiple choice question for a Nigerian professional skills assessment.

CONCEPT: {concept.concept_name}
DEFINITION: {concept.definition}
DIFFICULTY LEVEL: {level}
NIGERIAN CONTEXT: {context}
QUESTION TEMPLATE: {template}

WRONG ANSWER OPTIONS (distractors):
1. {wrong_answers[0] if len(wrong_answers) > 0 else 'Wrong answer 1'}
2. {wrong_answers[1] if len(wrong_answers) > 1 else 'Wrong answer 2'}
3. {wrong_answers[2] if len(wrong_answers) > 2 else 'Wrong answer 3'}

Create ONE clear, professional multiple choice question following the template.
- Use the Nigerian context provided
- Make it appropriate for {level} level
- Include exactly 4 options: A, B, C, D
- One correct answer, three plausible but wrong distractors
- No trick questions
- Beginner-friendly language

Format EXACTLY as:
QUESTION: [question text]
A) [option A]
B) [option B]
C) [option C]
D) [option D]
CORRECT: [A/B/C/D]
EXPLANATION: [one sentence why correct answer is right]
"""
    
    try:
        response = gemini_model.generate_content(prompt)
        text = response.text
        
        # Parse response
        lines = text.strip().split('\n')
        result = {'question': '', 'options': {}, 'correct': '', 'explanation': ''}
        
        for line in lines:
            line = line.strip()
            if line.startswith('QUESTION:'):
                result['question'] = line.replace('QUESTION:', '').strip()
            elif line.startswith('A)'):
                result['options']['A'] = line[2:].strip()
            elif line.startswith('B)'):
                result['options']['B'] = line[2:].strip()
            elif line.startswith('C)'):
                result['options']['C'] = line[2:].strip()
            elif line.startswith('D)'):
                result['options']['D'] = line[2:].strip()
            elif line.startswith('CORRECT:'):
                result['correct'] = line.replace('CORRECT:', '').strip()
            elif line.startswith('EXPLANATION:'):
                result['explanation'] = line.replace('EXPLANATION:', '').strip()
        
        return result
    except Exception as e:
        print(f"Gemini error: {e}")
        return None


@router.post("/start", response_model=SimulationStartResponse, status_code=status.HTTP_201_CREATED)
async def start_simulation(
    start_data: SimulationStart,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Start a new simulation session"""
    # Check cooldown
    cooldown = check_cooldown(db, current_user.user_id, start_data.job_type_id, start_data.level)
    if not cooldown.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": cooldown.reason,
                "next_available_at": cooldown.next_available_at.isoformat() if cooldown.next_available_at else None,
                "hours_remaining": cooldown.hours_remaining
            }
        )
    
    # Check for existing active session
    existing = db.query(SimulationSession).filter(
        SimulationSession.user_id == current_user.user_id,
        SimulationSession.status.in_(["in_progress", "paused"])
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "ACTIVE_SESSION_EXISTS",
                "session_id": str(existing.session_id),
                "message": "You have an active simulation session"
            }
        )
    
    # Get job type info
    job_type = db.query(JobType).filter(JobType.job_type_id == start_data.job_type_id).first()
    if not job_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job type not found"
        )
    
    # Get attempt number
    last_attempt = db.query(CooldownTracking).filter(
        CooldownTracking.user_id == current_user.user_id,
        CooldownTracking.job_type_id == start_data.job_type_id,
        CooldownTracking.level == start_data.level
    ).order_by(CooldownTracking.attempt_number.desc()).first()
    
    attempt_number = (last_attempt.attempt_number + 1) if last_attempt else 1
    
    # Create session
    session = SimulationSession(
        user_id=current_user.user_id,
        job_type_id=start_data.job_type_id,
        level=start_data.level,
        status="in_progress",
        attempt_number=attempt_number
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Generate questions
    question_count = get_question_count(db, start_data.job_type_id, start_data.level)
    concepts = select_concepts(db, start_data.job_type_id, start_data.level, question_count, current_user.user_id)
    
    questions = []
    for i, concept in enumerate(concepts, 1):
        q_data = generate_question_with_gemini(concept, start_data.level, i)
        
        if q_data:
            question = SimulationQuestion(
                session_id=session.session_id,
                concept_area=concept.concept_key,
                question_type="core" if i <= int(question_count * 0.7) else "specific",
                question_text=q_data.get('question', 'Question text unavailable'),
                answer_options=q_data.get('options', {}),
                correct_answer=q_data.get('correct', 'A'),
                order_index=i
            )
            db.add(question)
            questions.append({
                "question_id": str(question.question_id),
                "order_index": i,
                "question_text": question.question_text,
                "answer_options": question.answer_options
            })
    
    db.commit()
    
    # Record cooldown tracking
    cooldown_record = CooldownTracking(
        user_id=current_user.user_id,
        job_type_id=start_data.job_type_id,
        level=start_data.level,
        attempt_number=attempt_number,
        next_available_at=datetime.utcnow() + timedelta(hours=get_cooldown_hours(start_data.level))
    )
    db.add(cooldown_record)
    db.commit()
    
    return SimulationStartResponse(
        session_id=session.session_id,
        job_type_name=job_type.name,
        level=start_data.level,
        total_questions=question_count,
        estimated_minutes=job_type.avg_simulation_minutes,
        cooldown_applies=not cooldown.allowed and cooldown.reason == "COOLDOWN_ACTIVE",
        first_question=questions[0] if questions else {}
    )


@router.post("/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(
    session_id: str,
    answer_data: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Submit answer for a question"""
    # Get session
    session = db.query(SimulationSession).filter(
        SimulationSession.session_id == session_id,
        SimulationSession.user_id == current_user.user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status not in ["in_progress", "paused"]:
        raise HTTPException(status_code=400, detail="Session is not active")
    
    # Get question
    question = db.query(SimulationQuestion).filter(
        SimulationQuestion.question_id == answer_data.question_id,
        SimulationQuestion.session_id == session_id
    ).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    if question.answered_at:
        raise HTTPException(status_code=400, detail="Question already answered")
    
    # Record answer
    question.worker_answer = answer_data.answer
    question.is_correct = (answer_data.answer == question.correct_answer)
    question.answered_at = datetime.utcnow()
    question.time_spent_seconds = answer_data.time_spent_seconds
    
    # Update session activity
    session.last_active_at = datetime.utcnow()
    
    db.commit()
    
    # Update Skill DNA
    dna_record = db.query(UserSkillDNA).filter(
        UserSkillDNA.user_id == current_user.user_id,
        UserSkillDNA.job_type_id == session.job_type_id,
        UserSkillDNA.concept_area == question.concept_area
    ).first()
    
    if not dna_record:
        dna_record = UserSkillDNA(
            user_id=current_user.user_id,
            job_type_id=session.job_type_id,
            concept_area=question.concept_area
        )
        db.add(dna_record)
    
    if question.is_correct:
        dna_record.pass_count += 1
    else:
        dna_record.fail_count += 1
    
    dna_record.last_updated = datetime.utcnow()
    db.commit()
    
    # Check if this was the last question
    total_questions = db.query(SimulationQuestion).filter(
        SimulationQuestion.session_id == session_id
    ).count()
    
    answered_questions = db.query(SimulationQuestion).filter(
        SimulationQuestion.session_id == session_id,
        SimulationQuestion.answered_at.isnot(None)
    ).count()
    
    # Calculate current score
    correct_count = db.query(SimulationQuestion).filter(
        SimulationQuestion.session_id == session_id,
        SimulationQuestion.is_correct == True
    ).count()
    
    current_score = (correct_count / answered_questions * 100) if answered_questions > 0 else 0
    
    # If last question, transition to mini-task
    if answered_questions >= total_questions:
        session.knowledge_score = current_score
        session.status = "paused"  # Waiting for mini-task
        db.commit()
        
        # Get mini-task description based on job type
        job_type = db.query(JobType).filter(JobType.job_type_id == session.job_type_id).first()
        
        return AnswerResponse(
            correct=question.is_correct,
            section_complete=True,
            knowledge_score=round(current_score, 1),
            next_section="mini_task",
            mini_task={
                "task_id": str(session.session_id),  # Use session_id as task_id
                "description": f"Complete the {job_type.name} mini-task",
                "submission_type": job_type.submission_type,
                "time_limit_minutes": 20
            },
            progress={"answered": answered_questions, "total": total_questions, "section": "knowledge"}
        )
    
    # Get next question
    next_q = db.query(SimulationQuestion).filter(
        SimulationQuestion.session_id == session_id,
        SimulationQuestion.answered_at.is_(None)
    ).order_by(SimulationQuestion.order_index).first()
    
    return AnswerResponse(
        correct=question.is_correct,
        next_question={
            "question_id": str(next_q.question_id),
            "order_index": next_q.order_index,
            "question_text": next_q.question_text,
            "answer_options": next_q.answer_options
        } if next_q else None,
        progress={"answered": answered_questions, "total": total_questions, "section": "knowledge"}
    )


@router.post("/{session_id}/mini-task", response_model=MiniTaskResponse)
async def submit_mini_task(
    session_id: str,
    submission_content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Submit mini-task"""
    session = db.query(SimulationSession).filter(
        SimulationSession.session_id == session_id,
        SimulationSession.user_id == current_user.user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Save file if provided
    file_url = None
    if file:
        # TODO: Upload to S3 or storage
        file_url = f"/uploads/{session_id}/{file.filename}"
    
    # Create submission
    job_type = db.query(JobType).filter(JobType.job_type_id == session.job_type_id).first()
    
    submission = TaskSubmission(
        session_id=session.session_id,
        user_id=current_user.user_id,
        job_type_id=session.job_type_id,
        task_description=f"Mini-task for {job_type.name}",
        submission_content=submission_content,
        file_url=file_url,
        evaluation_status="pending"
    )
    
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    # TODO: Trigger async evaluation
    # For now, mark as passed if knowledge score is high enough
    mini_task_passed = session.knowledge_score >= settings.KNOWLEDGE_PASS_THRESHOLD
    
    submission.passed = mini_task_passed
    submission.evaluation_status = "ai_completed"
    submission.auto_score = 80.0 if mini_task_passed else 50.0
    
    session.mini_task_passed = mini_task_passed
    session.mini_task_score = submission.auto_score
    session.overall_passed = (
        session.knowledge_score >= settings.KNOWLEDGE_PASS_THRESHOLD and mini_task_passed
    )
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    
    # Update user skill
    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.user_id,
        UserSkill.job_type_id == session.job_type_id
    ).first()
    
    if user_skill:
        user_skill.total_attempts += 1
        user_skill.last_simulation_at = datetime.utcnow()
        
        if session.overall_passed:
            user_skill.passed_attempts += 1
            user_skill.status = "active"
            
            # Promote rank if passed
            ranks = ["beginner", "intermediate", "advanced", "expert"]
            current_idx = ranks.index(user_skill.current_rank)
            if current_idx < len(ranks) - 1:
                user_skill.current_rank = ranks[current_idx + 1]
        
        db.commit()
    
    # Update cooldown tracking
    cooldown_record = db.query(CooldownTracking).filter(
        CooldownTracking.user_id == current_user.user_id,
        CooldownTracking.job_type_id == session.job_type_id,
        CooldownTracking.level == session.level,
        CooldownTracking.completed_at.is_(None)
    ).first()
    
    if cooldown_record:
        cooldown_record.completed_at = datetime.utcnow()
        cooldown_record.passed = session.overall_passed
        db.commit()
    
    return MiniTaskResponse(
        submission_id=submission.submission_id,
        status="evaluating" if not mini_task_passed else "completed",
        estimated_seconds=30
    )


@router.get("/{session_id}/results", response_model=SimulationResults)
async def get_results(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get simulation results"""
    session = db.query(SimulationSession).filter(
        SimulationSession.session_id == session_id,
        SimulationSession.user_id == current_user.user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != "completed":
        return SimulationResults(
            session_id=session.session_id,
            status="evaluating",
            overall_passed=False,
            scores={},
            rank={},
            skill_dna={},
            next_steps={"check_back_in_seconds": 10}
        )
    
    # Get Skill DNA
    dna_records = db.query(UserSkillDNA).filter(
        UserSkillDNA.user_id == current_user.user_id,
        UserSkillDNA.job_type_id == session.job_type_id
    ).all()
    
    chart_data = []
    strengths = []
    weaknesses = []
    
    for dna in dna_records:
        total = dna.pass_count + dna.fail_count
        strength = (dna.pass_count / total * 100) if total > 0 else 0
        
        chart_data.append({
            "concept": dna.concept_area.replace('_', ' ').title(),
            "strength": round(strength, 1)
        })
        
        if strength >= 70:
            strengths.append(dna.concept_area)
        elif strength < 40:
            weaknesses.append(dna.concept_area)
    
    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.user_id,
        UserSkill.job_type_id == session.job_type_id
    ).first()
    
    return SimulationResults(
        session_id=session.session_id,
        status="completed",
        overall_passed=session.overall_passed or False,
        scores={
            "knowledge": {
                "score": float(session.knowledge_score) if session.knowledge_score else 0,
                "passed": (session.knowledge_score or 0) >= settings.KNOWLEDGE_PASS_THRESHOLD
            },
            "mini_task": {
                "score": float(session.mini_task_score) if session.mini_task_score else 0,
                "passed": session.mini_task_passed or False
            },
            "overall": float((session.knowledge_score or 0) * 0.68 + (session.mini_task_score or 0) * 0.32)
        },
        rank={
            "previous": "beginner",  # TODO: Track previous rank
            "new": user_skill.current_rank if user_skill else "beginner",
            "promoted": session.overall_passed or False
        },
        skill_dna={
            "is_first_time": len(dna_records) <= 3,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "chart_data": chart_data
        },
        next_steps={
            "can_retake": False,
            "next_retake_available_at": None,
            "can_level_up": session.overall_passed or False,
            "explore_jobs_url": f"/jobs?skill={session.job_type_id}"
        }
    )


@router.post("/{session_id}/heartbeat")
async def session_heartbeat(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Keep session alive"""
    session = db.query(SimulationSession).filter(
        SimulationSession.session_id == session_id,
        SimulationSession.user_id == current_user.user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check inactivity
    elapsed = (datetime.utcnow() - session.last_active_at).total_seconds()
    timeout_seconds = settings.SESSION_TIMEOUT_MINUTES * 60
    
    if elapsed > timeout_seconds:
        session.status = "abandoned"
        db.commit()
        return {
            "session_active": False,
            "reason": "INACTIVITY_TIMEOUT",
            "regenerated": True,
            "message": "Session expired due to inactivity"
        }
    
    # Update activity
    session.last_active_at = datetime.utcnow()
    db.commit()
    
    time_remaining = timeout_seconds - elapsed
    
    return {
        "session_active": True,
        "time_remaining_seconds": int(time_remaining),
        "warning": time_remaining < 300  # Warn if < 5 minutes
    }
