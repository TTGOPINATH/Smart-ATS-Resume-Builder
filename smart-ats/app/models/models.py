from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    ats_scans_used = Column(Integer, default=0)
    ats_scans_limit = Column(Integer, default=3)
    # Subscription tracking
    plan = Column(String(50), default="free")          # free | monthly | yearly
    plan_expires_at = Column(DateTime, nullable=True)  # None = no expiry set yet
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resumes = relationship("Resume", back_populates="owner", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False, default="My Resume")
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    linkedin = Column(String(500), nullable=True)
    github = Column(String(500), nullable=True)
    website = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    skills = Column(JSON, nullable=True, default=list)
    education = Column(JSON, nullable=True, default=list)
    experience = Column(JSON, nullable=True, default=list)
    projects = Column(JSON, nullable=True, default=list)
    certifications = Column(JSON, nullable=True, default=list)
    original_filename = Column(String(500), nullable=True)
    file_path = Column(String(1000), nullable=True)
    parsed_text = Column(Text, nullable=True)
    ats_score = Column(Float, nullable=True)
    ats_details = Column(JSON, nullable=True)
    last_job_description = Column(Text, nullable=True)
    pdf_path = Column(String(1000), nullable=True)
    download_count = Column(Integer, default=0)
    is_uploaded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="resumes")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    razorpay_order_id = Column(String(255), unique=True, nullable=True)
    razorpay_payment_id = Column(String(255), nullable=True)
    razorpay_signature = Column(String(500), nullable=True)
    amount = Column(Float, nullable=False)          # in INR (not paise)
    currency = Column(String(10), default="INR")
    plan = Column(String(50), nullable=False)       # monthly | yearly
    status = Column(String(50), default="pending")  # pending | success | failed | refunded
    failure_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="payments")
