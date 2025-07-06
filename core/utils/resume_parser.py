# core/utils/resume_parser.py

import re
import os
from pdfminer.high_level import extract_text
from docx import Document

def extract_text_from_file(filepath):
    if filepath.endswith('.pdf'):
        return extract_text(filepath)
    elif filepath.endswith('.docx'):
        doc = Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        return ""

def parse_resume(file_path):
    text = extract_text_from_file(file_path)

    # Heuristic for name extraction: assume it's the first non-empty line.
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    full_name = lines[0] if lines else ''

    # Regex-based extraction for other details
    email_match = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    phone_match = re.findall(r"\+?\d[\d -]{8,}\d", text)
    linkedin_match = re.findall(r"https?://(www\.)?linkedin\.com/in/[^\s]+", text)
    github_match = re.findall(r"https?://(www\.)?github\.com/[^\s]+", text)

    # If the name looks like an email, it's probably wrong. Try the second line.
    if '@' in full_name and len(lines) > 1:
        full_name = lines[1]

    # Heuristic for position and company extraction
    position = ''
    company = ''
    for line in lines:
        if not position and re.search(r'(?i)\b(position|title|role)\b', line):
            position = line
        if not company and re.search(r'(?i)\b(company|employer|organization|organisation|firm|inc|ltd|corp|solutions|technologies|systems|labs|university|college|school)\b', line):
            company = line
        if position and company:
            break

    # --- New: Extract bio/summary, education, and employment sections ---
    bio = ''
    education = []
    employment = []
    # Find summary/objective section (bio)
    bio_match = re.search(r'(?i)(summary|objective)\s*[:\-\n]+(.+?)(\n\s*\n|\n[A-Z][A-Za-z ]{2,}:|$)', text, re.DOTALL)
    if bio_match:
        bio = bio_match.group(2).strip()
    else:
        # If no explicit section, use first 3-5 lines after name if they look like a paragraph
        if len(lines) > 2:
            possible_bio = '\n'.join(lines[1:5])
            if len(possible_bio.split()) > 10:
                bio = possible_bio
    # Find education section
    edu_match = re.search(r'(?i)(education|academic background|qualifications)\s*[:\-\n]+(.+?)(\n\s*\n|\n[A-Z][A-Za-z ]{2,}:|$)', text, re.DOTALL)
    if edu_match:
        edu_text = edu_match.group(2).strip()
        # Split by lines, filter out empty
        education = [l.strip() for l in edu_text.split('\n') if l.strip()]
    # Find experience/employment section
    exp_match = re.search(r'(?i)(experience|employment|work history|professional experience)\s*[:\-\n]+(.+?)(\n\s*\n|\n[A-Z][A-Za-z ]{2,}:|$)', text, re.DOTALL)
    if exp_match:
        exp_text = exp_match.group(2).strip()
        employment = [l.strip() for l in exp_text.split('\n') if l.strip()]

    return {
        'full_name': full_name,
        'email': email_match,
        'phone': phone_match,
        'linkedin': linkedin_match[0] if linkedin_match else '',
        'github': github_match[0] if github_match else '',
        'position': position,
        'company': company,
        'bio': bio,
        'education': education,
        'employment': employment,
    }
