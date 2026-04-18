import os
import uuid
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, Resume
from app.schemas.schemas import ResumeCreate, ResumeOut
from app.utils.auth import get_current_user
from app.services.parser import parse_resume_file
from app.services.pdf_generator import generate_resume_pdf

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "5242880"))  # 5MB
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt"
}


@router.get("/", response_model=List[ResumeOut])
def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Resume).filter(Resume.user_id == current_user.id).order_by(
        Resume.updated_at.desc()
    ).all()


@router.post("/", response_model=ResumeOut)
def create_resume(
    resume_data: ResumeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = Resume(
        user_id=current_user.id,
        title=resume_data.title or "My Resume",
        full_name=resume_data.full_name,
        email=resume_data.email,
        phone=resume_data.phone,
        location=resume_data.location,
        linkedin=resume_data.linkedin,
        github=resume_data.github,
        website=resume_data.website,
        summary=resume_data.summary,
        skills=resume_data.skills or [],
        education=resume_data.education or [],
        experience=resume_data.experience or [],
        projects=resume_data.projects or [],
        certifications=resume_data.certifications or []
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(
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
    return resume


@router.put("/{resume_id}", response_model=ResumeOut)
def update_resume(
    resume_id: int,
    resume_data: ResumeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    fields = ["title", "full_name", "email", "phone", "location", "linkedin",
              "github", "website", "summary", "skills", "education",
              "experience", "projects", "certifications"]
    for field in fields:
        val = getattr(resume_data, field, None)
        if val is not None:
            setattr(resume, field, val)

    db.commit()
    db.refresh(resume)
    return resume


@router.delete("/{resume_id}")
def delete_resume(
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
    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted"}


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 5MB)")

    # Validate file type
    filename = file.filename or "resume"
    if not (filename.lower().endswith(".pdf") or
            filename.lower().endswith(".docx") or
            filename.lower().endswith(".txt")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: PDF, DOCX, TXT"
        )

    # Save file
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse
    parsed = parse_resume_file(content, filename)

    # Create resume record
    resume = Resume(
        user_id=current_user.id,
        title=f"Uploaded: {filename}",
        full_name=parsed.get("full_name"),
        email=parsed.get("email"),
        phone=parsed.get("phone"),
        linkedin=parsed.get("linkedin"),
        github=parsed.get("github"),
        skills=parsed.get("skills", []),
        parsed_text=parsed.get("raw_text", ""),
        original_filename=filename,
        file_path=file_path,
        is_uploaded=True
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/{resume_id}/download-pdf")
def download_pdf(
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

    # Watermark for free users
    add_watermark = not current_user.is_premium

    resume_dict = {
        "full_name": resume.full_name,
        "email": resume.email,
        "phone": resume.phone,
        "location": resume.location,
        "linkedin": resume.linkedin,
        "github": resume.github,
        "website": resume.website,
        "summary": resume.summary,
        "skills": resume.skills or [],
        "education": resume.education or [],
        "experience": resume.experience or [],
        "projects": resume.projects or [],
        "certifications": resume.certifications or []
    }

    try:
        pdf_bytes = generate_resume_pdf(resume_dict, watermark=add_watermark)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    # Track downloads
    resume.download_count = (resume.download_count or 0) + 1
    db.commit()

    safe_name = (resume.title or "resume").replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}.pdf"',
            "Content-Length": str(len(pdf_bytes))
        }
    )
