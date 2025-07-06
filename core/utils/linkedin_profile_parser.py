import re
import spacy

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# Rule-based keyword sets
education_keywords = ['university', 'college', 'institute', 'school', 'studied', 'graduated', 'msc', 'bsc', 'b.e', 'm.e']
employment_keywords = ['working', 'employed', 'at', 'intern', 'manager', 'engineer', 'developer', 'founder', 'ceo']
followers_pattern = r'(\d{2,4}\+?\s+(followers|connections))'
email_pattern = r'[\w\.-]+@[\w\.-]+'  # Simple email regex
phone_pattern = r'\b\d{10,}\b'  # Simple phone regex (10+ digits)

# Clean text
def clean_text(text):
    return re.sub(r'\s+', ' ', text.lower().strip())

# Rule-based extraction
def extract_education_rule(text):
    return [line.strip() for line in text.split('.') if any(kw in line for kw in education_keywords)]

def extract_employment_rule(text):
    return [line.strip() for line in text.split('.') if any(kw in line for kw in employment_keywords)]

def extract_followers_rule(text):
    match = re.search(followers_pattern, text.lower())
    return match.group() if match else "N/A"

def extract_contact_rule(text):
    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)
    return {'emails': emails or ["N/A"], 'phones': phones or ["N/A"]}

# SpaCy fallback NER
def extract_entities_spacy(text):
    doc = nlp(text)
    education = []
    employment = []
    for ent in doc.ents:
        if ent.label_ == "ORG":
            employment.append(ent.text)
        elif ent.label_ == "GPE":
            education.append(ent.text)
    return list(set(education)), list(set(employment))

# Unified extractor
def extract_profile_fields(raw_bio_text):
    text = clean_text(raw_bio_text)
    # Rule-based first
    edu_lines = extract_education_rule(text)
    emp_lines = extract_employment_rule(text)
    followers = extract_followers_rule(text)
    contact = extract_contact_rule(raw_bio_text)
    # Fallback to NER if rule-based gives nothing
    if not edu_lines or not emp_lines:
        edu_fallback, emp_fallback = extract_entities_spacy(text)
    else:
        edu_fallback, emp_fallback = [], []
    # Final result combining rule and NER
    education = edu_lines if edu_lines else edu_fallback
    employment = emp_lines if emp_lines else emp_fallback
    return {
        "Education": education or ["N/A"],
        "Employment": employment or ["N/A"],
        "Followers": followers,
        "Contact": contact
    } 