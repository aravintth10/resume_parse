import re
import spacy

nlp = spacy.load("en_core_web_sm")

def clean(text):
    return re.sub(r'\s+', ' ', text.strip().lower())

def extract_linkedin_fields(text):
    text = clean(text)
    # Education
    education_keywords = ['university', 'college', 'school', 'institute']
    education = [line.strip() for line in text.split('.') if any(kw in line for kw in education_keywords)]
    # Employment
    employment_keywords = ['at', 'engineer', 'developer', 'manager', 'ceo', 'founder']
    employment = [line.strip() for line in text.split('.') if any(kw in line for kw in employment_keywords)]
    # Bio = 1st 2 lines (or tweak later)
    bio = text.split('.')[:2]
    # Followers (Connections)
    match = re.search(r'(\d{2,4}\+?\s+(followers|connections))', text)
    connections = match.group() if match else "N/A"
    return {
        "Bio": ' '.join(bio) if bio else "N/A",
        "Education": education or ["N/A"],
        "Employment": employment or ["N/A"],
        "Connections": connections
    }

def extract_instagram_fields(text):
    text = clean(text)
    # Followers
    match = re.search(r'(\d{1,4}[kKmM]?\s*followers)', text)
    followers = match.group() if match else "N/A"
    # Posts
    posts_match = re.findall(r'\d+\s*posts?', text)
    posts = posts_match[0] if posts_match else "N/A"
    return {
        "Followers": followers,
        "Posts": posts
    } 