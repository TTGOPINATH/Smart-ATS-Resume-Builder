import io
import os
from typing import Optional
from datetime import datetime


def generate_resume_pdf(resume_data: dict, watermark: bool = False) -> bytes:
    """
    Generate ATS-friendly PDF resume using ReportLab.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm, inch
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
            Table, TableStyle, KeepTogether
        )
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )

        styles = getSampleStyleSheet()
        story = []

        # Custom styles
        name_style = ParagraphStyle(
            'NameStyle', parent=styles['Normal'],
            fontSize=22, fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=2, leading=26
        )
        contact_style = ParagraphStyle(
            'ContactStyle', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica',
            textColor=colors.HexColor('#555555'),
            spaceAfter=2, leading=13
        )
        section_header_style = ParagraphStyle(
            'SectionHeader', parent=styles['Normal'],
            fontSize=11, fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1a1a2e'),
            spaceBefore=8, spaceAfter=3, leading=14,
            borderPad=2
        )
        body_style = ParagraphStyle(
            'BodyStyle', parent=styles['Normal'],
            fontSize=9.5, fontName='Helvetica',
            textColor=colors.HexColor('#333333'),
            spaceAfter=3, leading=13
        )
        bold_body_style = ParagraphStyle(
            'BoldBodyStyle', parent=styles['Normal'],
            fontSize=9.5, fontName='Helvetica-Bold',
            textColor=colors.HexColor('#222222'),
            spaceAfter=1, leading=13
        )
        bullet_style = ParagraphStyle(
            'BulletStyle', parent=styles['Normal'],
            fontSize=9.5, fontName='Helvetica',
            textColor=colors.HexColor('#444444'),
            spaceAfter=2, leading=13,
            leftIndent=10, bulletIndent=0
        )
        italic_style = ParagraphStyle(
            'ItalicStyle', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Oblique',
            textColor=colors.HexColor('#666666'),
            spaceAfter=2, leading=12
        )

        def section_divider():
            return HRFlowable(
                width="100%", thickness=1,
                color=colors.HexColor('#3a86ff'),
                spaceAfter=4, spaceBefore=2
            )

        def thin_divider():
            return HRFlowable(
                width="100%", thickness=0.3,
                color=colors.HexColor('#cccccc'),
                spaceAfter=4, spaceBefore=4
            )

        # ── Header / Name ──────────────────────────────────────
        name = resume_data.get("full_name") or "Your Name"
        story.append(Paragraph(name, name_style))

        # Contact line
        contact_parts = []
        for field in ["email", "phone", "location"]:
            val = resume_data.get(field, "")
            if val:
                contact_parts.append(val)
        for field in ["linkedin", "github", "website"]:
            val = resume_data.get(field, "")
            if val:
                # Shorten URLs for display
                display = val.replace("https://", "").replace("http://", "")
                contact_parts.append(display)

        if contact_parts:
            contact_text = "  |  ".join(contact_parts)
            story.append(Paragraph(contact_text, contact_style))

        story.append(Spacer(1, 4*mm))
        story.append(section_divider())

        # ── Summary ────────────────────────────────────────────
        summary = resume_data.get("summary", "")
        if summary and summary.strip():
            story.append(Paragraph("PROFESSIONAL SUMMARY", section_header_style))
            story.append(thin_divider())
            story.append(Paragraph(summary, body_style))
            story.append(Spacer(1, 3*mm))

        # ── Experience ─────────────────────────────────────────
        experience = resume_data.get("experience") or []
        if experience:
            story.append(Paragraph("WORK EXPERIENCE", section_header_style))
            story.append(thin_divider())
            for i, exp in enumerate(experience):
                if not isinstance(exp, dict):
                    continue
                role = exp.get("role", "")
                company = exp.get("company", "")
                start = exp.get("start_date", "")
                end = "Present" if exp.get("is_current") else exp.get("end_date", "")
                desc = exp.get("description", "")

                if role or company:
                    # Role and date on same line
                    date_str = f"{start} – {end}" if start else end
                    role_text = f"<b>{role}</b>"
                    story.append(Paragraph(role_text, bold_body_style))

                    company_date = f"{company}{'  |  ' + date_str if date_str else ''}"
                    story.append(Paragraph(company_date, italic_style))

                    if desc:
                        # Split into bullets if multi-line
                        bullets = [b.strip() for b in desc.split('\n') if b.strip()]
                        if len(bullets) > 1:
                            for bullet in bullets:
                                if not bullet.startswith('•'):
                                    bullet = '• ' + bullet
                                story.append(Paragraph(bullet, bullet_style))
                        else:
                            text = desc if desc.startswith('•') else '• ' + desc
                            story.append(Paragraph(text, bullet_style))

                    if i < len(experience) - 1:
                        story.append(Spacer(1, 3*mm))

            story.append(Spacer(1, 3*mm))

        # ── Education ──────────────────────────────────────────
        education = resume_data.get("education") or []
        if education:
            story.append(Paragraph("EDUCATION", section_header_style))
            story.append(thin_divider())
            for edu in education:
                if not isinstance(edu, dict):
                    continue
                institution = edu.get("institution", "")
                degree = edu.get("degree", "")
                field = edu.get("field", "")
                start_yr = edu.get("start_year", "")
                end_yr = edu.get("end_year", "")
                gpa = edu.get("gpa", "")

                degree_field = f"{degree}{', ' + field if field else ''}"
                if degree_field.strip():
                    story.append(Paragraph(f"<b>{degree_field}</b>", bold_body_style))

                inst_date = institution
                if start_yr or end_yr:
                    inst_date += f"  |  {start_yr}–{end_yr}" if start_yr else f"  |  {end_yr}"
                if gpa:
                    inst_date += f"  |  GPA: {gpa}"
                if inst_date.strip():
                    story.append(Paragraph(inst_date, italic_style))
                story.append(Spacer(1, 2*mm))

            story.append(Spacer(1, 1*mm))

        # ── Skills ─────────────────────────────────────────────
        skills = resume_data.get("skills") or []
        if skills:
            story.append(Paragraph("SKILLS", section_header_style))
            story.append(thin_divider())
            if isinstance(skills, list):
                skills_text = "  •  ".join(skills)
            else:
                skills_text = str(skills)
            story.append(Paragraph(skills_text, body_style))
            story.append(Spacer(1, 3*mm))

        # ── Projects ───────────────────────────────────────────
        projects = resume_data.get("projects") or []
        if projects:
            story.append(Paragraph("PROJECTS", section_header_style))
            story.append(thin_divider())
            for proj in projects:
                if not isinstance(proj, dict):
                    continue
                p_name = proj.get("name", "")
                p_desc = proj.get("description", "")
                p_tech = proj.get("technologies", "")
                p_url = proj.get("url", "")

                if p_name:
                    story.append(Paragraph(f"<b>{p_name}</b>", bold_body_style))
                if p_tech:
                    story.append(Paragraph(f"Technologies: {p_tech}", italic_style))
                if p_desc:
                    story.append(Paragraph(p_desc, body_style))
                if p_url:
                    url_display = p_url.replace("https://", "").replace("http://", "")
                    story.append(Paragraph(url_display, italic_style))
                story.append(Spacer(1, 2*mm))

        # ── Certifications ─────────────────────────────────────
        certs = resume_data.get("certifications") or []
        if certs:
            story.append(Paragraph("CERTIFICATIONS", section_header_style))
            story.append(thin_divider())
            for cert in certs:
                if not isinstance(cert, dict):
                    continue
                c_name = cert.get("name", "")
                c_issuer = cert.get("issuer", "")
                c_year = cert.get("year", "")
                if c_name:
                    cert_line = c_name
                    if c_issuer:
                        cert_line += f" — {c_issuer}"
                    if c_year:
                        cert_line += f" ({c_year})"
                    story.append(Paragraph(f"• {cert_line}", bullet_style))

        # ── Watermark ──────────────────────────────────────────
        if watermark:
            story.append(Spacer(1, 10*mm))
            wm_style = ParagraphStyle(
                'Watermark', parent=styles['Normal'],
                fontSize=8, fontName='Helvetica-Oblique',
                textColor=colors.HexColor('#aaaaaa'),
                alignment=TA_CENTER
            )
            story.append(Paragraph(
                "Generated by Smart ATS Resume Builder — Upgrade to Pro to remove watermark",
                wm_style
            ))

        doc.build(story)
        return buffer.getvalue()

    except ImportError:
        # Fallback: generate simple text-based PDF
        return _generate_text_pdf(resume_data, watermark)
    except Exception as e:
        raise Exception(f"PDF generation failed: {str(e)}")


def _generate_text_pdf(resume_data: dict, watermark: bool = False) -> bytes:
    """Simple fallback PDF using raw PDF syntax."""
    name = resume_data.get("full_name", "Resume")
    content = f"Resume: {name}\n\nGenerated by Smart ATS Resume Builder"
    # Return minimal valid PDF
    pdf = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 44>>
stream
BT /F1 12 Tf 72 750 Td (""" + name.encode() + b""") Tj ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000360 00000 n
trailer<</Size 6/Root 1 0 R>>
startxref
441
%%EOF"""
    return pdf
