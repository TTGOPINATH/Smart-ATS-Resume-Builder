from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, Resume
from app.schemas.schemas import ATSRequest, ATSResult
from app.utils.auth import get_current_user
from app.services.ats_engine import calculate_ats_score, generate_ai_suggestions

router = APIRouter()

FREE_SCAN_LIMIT = 3


@router.post("/score")
def score_resume(
    request: ATSRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check scan limit for free users
    if not current_user.is_premium:
        if current_user.ats_scans_used >= current_user.ats_scans_limit:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "scan_limit_reached",
                    "message": f"Free plan allows {FREE_SCAN_LIMIT} ATS scans. Upgrade to Pro for unlimited scans.",
                    "scans_used": current_user.ats_scans_used,
                    "scans_limit": current_user.ats_scans_limit
                }
            )

    # Get resume
    resume = db.query(Resume).filter(
        Resume.id == request.resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Build resume data dict
    resume_data = {
        "full_name": resume.full_name,
        "email": resume.email,
        "phone": resume.phone,
        "location": resume.location,
        "linkedin": resume.linkedin,
        "github": resume.github,
        "summary": resume.summary,
        "skills": resume.skills or [],
        "education": resume.education or [],
        "experience": resume.experience or [],
        "projects": resume.projects or [],
        "certifications": resume.certifications or []
    }

    # If uploaded, also use parsed text
    if resume.is_uploaded and resume.parsed_text:
        resume_data["_raw_text"] = resume.parsed_text

    # Calculate score
    result = calculate_ats_score(resume_data, request.job_description or "")

    # Save to resume
    resume.ats_score = result["total_score"]
    resume.ats_details = result
    if request.job_description:
        resume.last_job_description = request.job_description

    # Increment scan count for free users
    if not current_user.is_premium:
        current_user.ats_scans_used += 1

    db.commit()

    return {
        **result,
        "scans_remaining": (
            "unlimited" if current_user.is_premium
            else max(0, current_user.ats_scans_limit - current_user.ats_scans_used)
        )
    }


@router.post("/optimize")
def optimize_resume(
    request: ATSRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Premium only
    if not current_user.is_premium:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "premium_required",
                "message": "AI Resume Optimization is a Pro feature. Upgrade to unlock."
            }
        )

    resume = db.query(Resume).filter(
        Resume.id == request.resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_data = {
        "full_name": resume.full_name,
        "summary": resume.summary,
        "skills": resume.skills or [],
        "experience": resume.experience or [],
        "projects": resume.projects or []
    }

    suggestions = generate_ai_suggestions(resume_data, request.job_description or "")
    return suggestions


@router.get("/history/{resume_id}")
def get_ats_history(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {
        "resume_id": resume_id,
        "title": resume.title,
        "ats_score": resume.ats_score,
        "ats_details": resume.ats_details,
        "last_job_description": resume.last_job_description,
        "updated_at": resume.updated_at
    }
