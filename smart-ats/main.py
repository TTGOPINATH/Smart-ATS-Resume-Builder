import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()

from app.database import engine, Base
from app.routes import auth, resume, ats, payment, admin

# Create all tables
Base.metadata.create_all(bind=engine)

# Create uploads directory
os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="Smart ATS Resume Builder & Optimizer",
    description="AI-powered resume builder with ATS optimization",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(resume.router, prefix="/resume", tags=["Resume"])
app.include_router(ats.router, prefix="/ats", tags=["ATS"])
app.include_router(payment.router, prefix="/payment", tags=["Payment"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/builder", response_class=HTMLResponse)
async def builder(request: Request):
    return templates.TemplateResponse("builder.html", {"request": request})


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/results", response_class=HTMLResponse)
async def results_page(request: Request):
    return templates.TemplateResponse("results.html", {"request": request})


@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/admin/panel", response_class=HTMLResponse)
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/payment/success", response_class=HTMLResponse)
async def payment_success_page(request: Request):
    return templates.TemplateResponse("payment_success.html", {"request": request})


app.run(host="0.0.0.0", port=10000)
