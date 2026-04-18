# 🧠 Smart ATS Resume Builder & Optimizer

A complete, production-ready, AI-powered resume builder with ATS scoring, job description matching, and Razorpay payments.

---

## 📁 Project Structure

```
smart-ats/
├── main.py                        # FastAPI app entry point
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variable template
├── app/
│   ├── database.py                # SQLAlchemy engine + session
│   ├── models/
│   │   └── models.py              # User, Resume, Payment ORM models
│   ├── schemas/
│   │   └── schemas.py             # Pydantic request/response schemas
│   ├── routes/
│   │   ├── auth.py                # Register, Login, /me
│   │   ├── resume.py              # CRUD, Upload, PDF Download
│   │   ├── ats.py                 # ATS Score, AI Optimize
│   │   ├── payment.py             # Razorpay Orders + Verify
│   │   └── admin.py               # Admin stats, user management
│   ├── services/
│   │   ├── ats_engine.py          # ATS scoring algorithm
│   │   ├── parser.py              # PDF/DOCX resume parser
│   │   └── pdf_generator.py       # ReportLab PDF generation
│   └── utils/
│       └── auth.py                # JWT + bcrypt utilities
├── templates/
│   ├── base.html                  # Shared layout + navbar
│   ├── landing.html               # Homepage
│   ├── login.html                 # Sign in
│   ├── register.html              # Sign up
│   ├── dashboard.html             # User dashboard
│   ├── builder.html               # Multi-step resume builder
│   ├── upload.html                # Resume upload page
│   ├── results.html               # ATS score + AI optimizer
│   ├── pricing.html               # Plans + Razorpay checkout
│   └── admin.html                 # Admin panel
├── static/
│   ├── css/main.css               # Full stylesheet
│   └── js/app.js                  # Auth, API, Toast utilities
└── uploads/                       # Uploaded resume files (auto-created)
```

---

## ⚡ Quick Start (Local Development)

### 1. Clone and enter the project
```bash
cd smart-ats
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your values (see below)
```

### 5. Run the server
```bash
uvicorn main:app --reload --port 8000
```

### 6. Open in browser
```
http://localhost:8000
```

---

## 🔧 Environment Variables

Create a `.env` file based on `.env.example`:

```env
# JWT Auth
SECRET_KEY=your-super-secret-key-minimum-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080   # 7 days

# Database
DATABASE_URL=sqlite:///./smart_ats.db

# Razorpay (get from https://dashboard.razorpay.com)
RAZORPAY_KEY_ID=rzp_test_XXXXXXXXXXXX
RAZORPAY_KEY_SECRET=XXXXXXXXXXXXXXXXXXXX

# Upload settings
UPLOAD_DIR=uploads
MAX_FILE_SIZE=5242880   # 5MB in bytes

# Environment
ENVIRONMENT=development
```

---

## 💳 Razorpay Payment Integration

### Step 1: Create Razorpay Account
1. Go to https://razorpay.com
2. Sign up and complete KYC (for live payments)
3. For testing, use Test Mode

### Step 2: Get API Keys
1. Dashboard → Settings → API Keys
2. Generate Key ID and Key Secret
3. Copy to your `.env` file

### Step 3: Test Payment
- Use card number: `4111 1111 1111 1111`
- Any future expiry date
- Any 3-digit CVV

### Step 4: Webhook (optional for production)
- Dashboard → Webhooks → Add Endpoint
- URL: `https://yourdomain.com/payment/webhook`
- Events: `payment.captured`

---

## 🔌 API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create account, returns JWT |
| POST | `/auth/login` | Sign in, returns JWT |
| GET | `/auth/me` | Get current user |

### Resume
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/resume/` | List all user resumes |
| POST | `/resume/` | Create new resume |
| GET | `/resume/{id}` | Get single resume |
| PUT | `/resume/{id}` | Update resume |
| DELETE | `/resume/{id}` | Delete resume |
| POST | `/resume/upload` | Upload PDF/DOCX |
| GET | `/resume/{id}/download-pdf` | Download PDF |

### ATS
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ats/score` | Run ATS analysis |
| POST | `/ats/optimize` | AI suggestions (Pro only) |
| GET | `/ats/history/{id}` | ATS score history |

### Payment
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/payment/plans` | Get available plans |
| POST | `/payment/create-order` | Create Razorpay order |
| POST | `/payment/verify` | Verify payment signature |
| GET | `/payment/history` | User payment history |

### Admin (requires admin user)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/stats` | Platform statistics |
| GET | `/admin/users` | List all users |
| PUT | `/admin/users/{id}/toggle-premium` | Toggle Pro status |
| PUT | `/admin/users/{id}/toggle-active` | Enable/disable user |
| GET | `/admin/payments` | All payments |

---

## 🛡️ Creating an Admin User

After registration, manually set `is_admin = true` in the database:

```bash
# Using SQLite CLI
sqlite3 smart_ats.db
UPDATE users SET is_admin = 1 WHERE email = 'admin@yourdomain.com';
.quit
```

Then access the admin panel at: `/admin/panel`

---

## 🚀 Deployment

### Option A: Render.com (Recommended)

1. Push your code to GitHub
2. Go to https://render.com → New Web Service
3. Connect your GitHub repo
4. Set:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables in Render dashboard
6. Deploy!

### Option B: Railway.app

1. Push to GitHub
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Add environment variables
4. Railway auto-detects Python and deploys

### Option C: VPS / Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN mkdir -p uploads
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t smart-ats .
docker run -p 8000:8000 --env-file .env smart-ats
```

---

## 💡 ATS Scoring Algorithm

The ATS score (0–100) is calculated as:

| Component | Weight | How Calculated |
|-----------|--------|----------------|
| **Keyword Match** | 40% | Overlap between resume keywords and JD keywords |
| **Section Completeness** | 20% | Which sections are filled (name, email, summary, skills, etc.) |
| **Formatting/Readability** | 20% | Word count, contact info, quantified achievements |
| **JD Match** | 20% | Action verb match + skill overlap with job description |

**Grade Scale**:
- A (85–100): Excellent ATS compatibility
- B (70–84): Good, minor improvements needed
- C (55–69): Average, significant gaps
- D (40–54): Below average, needs rewrite
- F (0–39): Poor, major optimization required

---

## 🆓 Free vs Pro Features

| Feature | Free | Pro |
|---------|------|-----|
| Resume builder | ✅ Unlimited | ✅ Unlimited |
| ATS scans | 3 total | ✅ Unlimited |
| PDF download | ✅ Watermarked | ✅ Clean PDF |
| Resume upload & parse | ✅ | ✅ |
| Job description matching | ✅ | ✅ |
| AI Resume Optimizer | ❌ | ✅ |
| Resume history | ✅ | ✅ |
| Priority support | ❌ | ✅ |

---

## 🧪 Running Tests

```bash
pip install pytest httpx
pytest tests/ -v
```

---

## 📦 Key Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `sqlalchemy` | ORM / database |
| `python-jose` | JWT tokens |
| `passlib[bcrypt]` | Password hashing |
| `pdfminer.six` | PDF text extraction |
| `python-docx` | DOCX parsing |
| `reportlab` | PDF generation |
| `razorpay` | Payment SDK |
| `jinja2` | HTML templates |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/amazing`
3. Commit: `git commit -m 'Add amazing feature'`
4. Push and open a Pull Request

---

## 📄 License

MIT License. Free for personal and commercial use.
