# core/utils/confidence_score.py

from difflib import SequenceMatcher
import face_recognition

def score_name_match(input_name, scraped_name):
    """Simple string similarity score"""
    if not input_name or not scraped_name:
        return 0
    return round(SequenceMatcher(None, input_name.lower(), scraped_name.lower()).ratio() * 100, 2)

def score_email_match(input_emails, scraped_emails):
    return 100 if set(input_emails) & set(scraped_emails) else 0

def score_phone_match(input_phones, scraped_phones):
    return 100 if set(input_phones) & set(scraped_phones) else 0

def score_linkedin_match(input_url, scraped_url):
    return 100 if input_url == scraped_url else 0

def score_github_match(input_url, scraped_url):
    return 100 if input_url == scraped_url else 0

def score_activity(posts, followers, threshold=10):
    """Simple heuristic for activity"""
    score = 0
    if posts > threshold:
        score += 50
    if followers > threshold * 10:
        score += 50
    return score

def score_image_match(candidate_image_path, scraped_image_path):
    try:
        image1 = face_recognition.load_image_file(candidate_image_path)
        image2 = face_recognition.load_image_file(scraped_image_path)

        encodings1 = face_recognition.face_encodings(image1)
        encodings2 = face_recognition.face_encodings(image2)

        if not encodings1 or not encodings2:
            return 0

        result = face_recognition.compare_faces([encodings1[0]], encodings2[0])
        return 100 if result[0] else 0
    except Exception as e:
        print(f"[Image Match Error]: {e}")
        return 0

def calculate_final_score(criteria_scores, weights=None):
    if weights is None:
        # Default equal weights
        weights = {
            'name': 0.15,
            'email': 0.15,
            'phone': 0.10,
            'linkedin': 0.10,
            'github': 0.10,
            'activity': 0.15,
            'image': 0.25
        }
    final_score = 0
    for key in criteria_scores:
        final_score += criteria_scores[key] * weights.get(key, 0)
    return round(final_score, 2)
