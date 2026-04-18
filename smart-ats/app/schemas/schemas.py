from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime


# ── Auth Schemas ──────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_premium: bool
    is_admin: bool
    ats_scans_used: int
    ats_scans_limit: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


# ── Resume Schemas ────────────────────────────────────────────────
class EducationItem(BaseModel):
    institution: str = ""
    degree: str = ""
    field: str = ""
    start_year: str = ""
    end_year: str = ""
    gpa: str = ""


class ExperienceItem(BaseModel):
    company: str = ""
    role: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""
    is_current: bool = False


class ProjectItem(BaseModel):
    name: str = ""
    description: str = ""
    technologies: str = ""
    url: str = ""


class CertificationItem(BaseModel):
    name: str = ""
    issuer: str = ""
    year: str = ""


class ResumeCreate(BaseModel):
    title: Optional[str] = "My Resume"
    full_name: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    location: Optional[str] = ""
    linkedin: Optional[str] = ""
    github: Optional[str] = ""
    website: Optional[str] = ""
    summary: Optional[str] = ""
    skills: Optional[List[str]] = []
    education: Optional[List[dict]] = []
    experience: Optional[List[dict]] = []
    projects: Optional[List[dict]] = []
    certifications: Optional[List[dict]] = []


class ResumeOut(BaseModel):
    id: int
    title: str
    full_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    linkedin: Optional[str]
    github: Optional[str]
    website: Optional[str]
    summary: Optional[str]
    skills: Optional[Any]
    education: Optional[Any]
    experience: Optional[Any]
    projects: Optional[Any]
    certifications: Optional[Any]
    ats_score: Optional[float]
    is_uploaded: bool
    download_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── ATS Schemas ───────────────────────────────────────────────────
class ATSRequest(BaseModel):
    resume_id: int
    job_description: Optional[str] = ""


class ATSResult(BaseModel):
    total_score: float
    keyword_score: float
    completeness_score: float
    formatting_score: float
    jd_match_score: float
    missing_keywords: List[str]
    present_keywords: List[str]
    suggestions: List[str]
    section_scores: dict
    grade: str


# ── Payment Schemas ───────────────────────────────────────────────
class CreateOrderRequest(BaseModel):
    plan: str  # monthly or yearly


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan: str
