import re
import json
from typing import List, Dict, Any, Optional

# Industry keywords by category
TECH_KEYWORDS = [
    "python", "javascript", "java", "c++", "c#", "react", "angular", "vue",
    "nodejs", "django", "fastapi", "flask", "spring", "sql", "mysql", "postgresql",
    "mongodb", "redis", "docker", "kubernetes", "aws", "azure", "gcp", "git",
    "agile", "scrum", "rest", "api", "machine learning", "deep learning", "nlp",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "data analysis",
    "ci/cd", "devops", "linux", "typescript", "graphql", "microservices"
]

SOFT_SKILLS = [
    "leadership", "communication", "teamwork", "problem solving", "analytical",
    "creative", "collaborative", "detail-oriented", "organized", "proactive",
    "adaptable", "mentoring", "presentation", "negotiation", "strategic"
]

RESUME_SECTIONS = ["summary", "experience", "education", "skills", "projects", "certifications"]


def extract_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from text."""
    text_lower = text.lower()
    found = []
    all_keywords = TECH_KEYWORDS + SOFT_SKILLS
    for kw in all_keywords:
        if kw in text_lower:
            found.append(kw)
    # Also extract capitalized words (likely proper nouns/technologies)
    words = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', text)
    for w in words:
        if w.lower() not in [k.lower() for k in found]:
            found.append(w.lower())
    return list(set(found))


def score_keywords(resume_text: str, job_description: str) -> Dict:
    """Score keyword matching between resume and job description."""
    if not job_description.strip():
        # Score based on tech keywords presence in resume
        resume_lower = resume_text.lower()
        present = [kw for kw in TECH_KEYWORDS if kw in resume_lower]
        missing = [kw for kw in TECH_KEYWORDS[:20] if kw not in resume_lower]
        score = min(40, len(present) * 2)
        return {
            "score": score,
            "present_keywords": present[:15],
            "missing_keywords": missing[:10]
        }

    jd_keywords = extract_keywords(job_description)
    resume_lower = resume_text.lower()

    present = []
    missing = []
    for kw in jd_keywords:
        if kw.lower() in resume_lower:
            present.append(kw)
        else:
            missing.append(kw)

    if not jd_keywords:
        return {"score": 20, "present_keywords": [], "missing_keywords": []}

    match_ratio = len(present) / len(jd_keywords) if jd_keywords else 0
    score = round(match_ratio * 40)

    return {
        "score": min(40, score),
        "present_keywords": present[:20],
        "missing_keywords": missing[:15]
    }


def score_completeness(resume_data: dict) -> Dict:
    """Score resume section completeness."""
    scores = {}
    total = 0

    checks = {
        "personal_info": {
            "weight": 4,
            "fields": ["full_name", "email", "phone", "location"],
            "label": "Personal Information"
        },
        "summary": {
            "weight": 3,
            "fields": ["summary"],
            "label": "Professional Summary"
        },
        "experience": {
            "weight": 5,
            "fields": ["experience"],
            "label": "Work Experience"
        },
        "education": {
            "weight": 3,
            "fields": ["education"],
            "label": "Education"
        },
        "skills": {
            "weight": 3,
            "fields": ["skills"],
            "label": "Skills"
        },
        "projects": {
            "weight": 2,
            "fields": ["projects"],
            "label": "Projects"
        }
    }

    max_score = sum(c["weight"] for c in checks.values())

    for key, config in checks.items():
        section_score = 0
        for field in config["fields"]:
            val = resume_data.get(field)
            if val:
                if isinstance(val, list) and len(val) > 0:
                    section_score += config["weight"]
                elif isinstance(val, str) and len(val.strip()) > 10:
                    section_score += config["weight"]
        scores[config["label"]] = min(config["weight"], section_score)
        total += min(config["weight"], section_score)

    normalized = round((total / max_score) * 20)
    return {"score": normalized, "section_scores": scores}


def score_formatting(resume_text: str, resume_data: dict) -> Dict:
    """Score resume formatting and readability."""
    score = 0
    issues = []

    # Check length (ideal: 400-800 words)
    words = len(resume_text.split()) if resume_text else 0
    if 300 <= words <= 900:
        score += 5
    elif words < 300:
        issues.append("Resume seems too short — aim for 400–700 words")
    else:
        issues.append("Resume may be too long — try to keep under 800 words")
        score += 2

    # Check contact info completeness
    if resume_data.get("email"):
        score += 2
    if resume_data.get("phone"):
        score += 2
    if resume_data.get("linkedin"):
        score += 2
    else:
        issues.append("Add your LinkedIn profile URL")

    # Check summary length
    summary = resume_data.get("summary", "")
    if summary and 50 <= len(summary) <= 500:
        score += 3
    elif not summary:
        issues.append("Add a professional summary (2-3 sentences)")

    # Check experience bullet points
    experience = resume_data.get("experience", [])
    if experience:
        for exp in experience:
            desc = exp.get("description", "") if isinstance(exp, dict) else ""
            if desc and len(desc) > 50:
                score += 1
                break

    # Check skills count
    skills = resume_data.get("skills", [])
    if isinstance(skills, list) and len(skills) >= 5:
        score += 3
    elif isinstance(skills, list) and len(skills) > 0:
        score += 1
        issues.append("Add more skills (aim for at least 8–10)")
    else:
        issues.append("Add a skills section with relevant technologies")

    # Check quantifiable achievements
    if resume_text:
        has_numbers = bool(re.search(r'\d+%|\$\d+|\d+ (people|team|users|customers|projects)', resume_text, re.I))
        if has_numbers:
            score += 3
        else:
            issues.append("Add quantifiable achievements (e.g., 'Increased sales by 30%')")

    return {"score": min(20, score), "issues": issues}


def score_jd_match(resume_text: str, job_description: str) -> Dict:
    """Score job description match."""
    if not job_description or not job_description.strip():
        return {"score": 10, "matched": [], "missing": []}

    # Extract key phrases from JD
    jd_lower = job_description.lower()
    resume_lower = resume_text.lower() if resume_text else ""

    # Common action verbs from JD
    action_verbs = re.findall(r'\b(develop|design|implement|manage|lead|create|build|analyze|optimize|deploy|maintain|collaborate|communicate|improve)\w*\b', jd_lower)
    action_verbs = list(set(action_verbs))[:10]

    matched_verbs = [v for v in action_verbs if v in resume_lower]

    # Extract noun phrases (skills/tools mentioned in JD)
    jd_skills = extract_keywords(job_description)
    resume_skills = extract_keywords(resume_text) if resume_text else []

    matched_skills = [s for s in jd_skills if s in resume_skills]
    missing_skills = [s for s in jd_skills if s not in resume_skills][:8]

    if jd_skills:
        match_ratio = len(matched_skills) / len(jd_skills)
        score = round(match_ratio * 20)
    else:
        score = 10

    return {
        "score": min(20, score),
        "matched": matched_skills[:10],
        "missing": missing_skills
    }


def calculate_ats_score(resume_data: dict, job_description: str = "") -> Dict:
    """
    Master ATS scoring function.
    Returns comprehensive scoring breakdown.
    """
    # Build full resume text
    parts = []
    for field in ["full_name", "email", "phone", "location", "summary"]:
        val = resume_data.get(field, "")
        if val:
            parts.append(str(val))

    for section in ["skills", "education", "experience", "projects", "certifications"]:
        items = resume_data.get(section, [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    parts.extend([str(v) for v in item.values() if v])
                elif isinstance(item, str):
                    parts.append(item)
        elif isinstance(items, str):
            parts.append(items)

    resume_text = " ".join(parts)

    # Score each component
    kw_result = score_keywords(resume_text, job_description)
    comp_result = score_completeness(resume_data)
    fmt_result = score_formatting(resume_text, resume_data)
    jd_result = score_jd_match(resume_text, job_description)

    total = kw_result["score"] + comp_result["score"] + fmt_result["score"] + jd_result["score"]
    total = min(100, total)

    # Grade
    if total >= 85:
        grade = "A"
    elif total >= 70:
        grade = "B"
    elif total >= 55:
        grade = "C"
    elif total >= 40:
        grade = "D"
    else:
        grade = "F"

    # Compile suggestions
    suggestions = []
    suggestions.extend(fmt_result.get("issues", []))

    if kw_result["score"] < 25:
        suggestions.append("Include more industry-relevant keywords from the job description")
    if comp_result["score"] < 15:
        suggestions.append("Complete all resume sections for a higher score")
    if not resume_data.get("projects"):
        suggestions.append("Add a projects section to showcase your work")
    if not resume_data.get("certifications"):
        suggestions.append("Consider adding relevant certifications")
    if jd_result["score"] < 10 and job_description:
        suggestions.append("Tailor your resume more closely to the job description")

    return {
        "total_score": total,
        "keyword_score": kw_result["score"],
        "completeness_score": comp_result["score"],
        "formatting_score": fmt_result["score"],
        "jd_match_score": jd_result["score"],
        "missing_keywords": kw_result.get("missing_keywords", []),
        "present_keywords": kw_result.get("present_keywords", []),
        "suggestions": suggestions[:8],
        "section_scores": comp_result.get("section_scores", {}),
        "grade": grade,
        "jd_matched": jd_result.get("matched", []),
        "jd_missing": jd_result.get("missing", [])
    }


def generate_ai_suggestions(resume_data: dict, job_description: str = "") -> Dict:
    """Generate AI-style improvement suggestions."""
    suggestions = {
        "summary_rewrite": "",
        "bullet_improvements": [],
        "skills_to_add": [],
        "keywords_to_add": [],
        "overall_tips": []
    }

    # Summary suggestions
    summary = resume_data.get("summary", "")
    if not summary:
        suggestions["summary_rewrite"] = (
            f"Results-driven {resume_data.get('full_name', 'professional')} with expertise in "
            "[your key skills]. Proven track record of [key achievement]. Seeking to leverage "
            "[skill set] to drive [goal] at a forward-thinking organization."
        )
    elif len(summary) < 100:
        suggestions["summary_rewrite"] = (
            summary + " Demonstrated ability to deliver high-impact results in fast-paced environments "
            "through strong technical expertise and collaborative leadership."
        )

    # Experience bullet improvements
    experience = resume_data.get("experience", [])
    for exp in (experience or [])[:3]:
        if isinstance(exp, dict):
            desc = exp.get("description", "")
            role = exp.get("role", "professional")
            if desc and not any(char.isdigit() for char in desc):
                suggestions["bullet_improvements"].append({
                    "original": desc[:100] + "..." if len(desc) > 100 else desc,
                    "improved": f"• Led {role.lower()} initiatives resulting in [X]% improvement in [metric]. "
                                f"Collaborated with cross-functional teams to deliver [outcome], "
                                f"reducing [problem] by [Y]% and increasing [positive metric] by [Z]%."
                })

    # Skills to add based on JD
    if job_description:
        jd_keywords = extract_keywords(job_description)
        current_skills = resume_data.get("skills", [])
        if isinstance(current_skills, list):
            current_lower = [s.lower() for s in current_skills]
            suggestions["keywords_to_add"] = [
                kw for kw in jd_keywords if kw.lower() not in current_lower
            ][:10]

    # General tips
    suggestions["overall_tips"] = [
        "Use strong action verbs: Led, Developed, Implemented, Optimized, Delivered",
        "Quantify achievements with numbers, percentages, and dollar amounts",
        "Keep resume to 1–2 pages maximum",
        "Use consistent date formatting (MM/YYYY or Month YYYY)",
        "Tailor your resume for each job application",
        "Ensure no typos or grammatical errors — proofread carefully",
        "Use bullet points for experience descriptions, not paragraphs",
        "Place most recent experience first (reverse chronological order)"
    ]

    return suggestions
