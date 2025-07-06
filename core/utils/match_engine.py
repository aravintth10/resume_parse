# core/utils/matching_engine.py

from .confidence_score import (
    score_name_match, score_email_match, score_phone_match,
    score_linkedin_match, score_github_match, score_activity,
    score_image_match, calculate_final_score
)

def evaluate_profile(user_input, scraped_profile):
    """Evaluate confidence score for one profile"""
    return {
        'platform': scraped_profile.get('platform'),
        'handle': scraped_profile.get('username'),
        'url': scraped_profile.get('profile_url'),
        'scores': {
            'name': score_name_match(user_input['full_name'], scraped_profile.get('full_name')),
            'email': score_email_match(user_input['emails'], scraped_profile.get('emails', [])),
            'phone': score_phone_match(user_input['phones'], scraped_profile.get('phones', [])),
            'linkedin': score_linkedin_match(user_input.get('linkedin'), scraped_profile.get('linkedin')),
            'github': score_github_match(user_input.get('github'), scraped_profile.get('github')),
            'activity': score_activity(scraped_profile.get('posts', 0), scraped_profile.get('followers', 0)),
            'image': score_image_match(user_input['image_path'], scraped_profile.get('image_path')),
        }
    }

def get_best_profile_match(user_input, scraped_profiles):
    """Evaluates all profiles and returns the best match"""
    evaluated_profiles = []

    for profile in scraped_profiles:
        result = evaluate_profile(user_input, profile)
        result['confidence'] = calculate_final_score(result['scores'])
        evaluated_profiles.append(result)

    # Sort by confidence descending
    evaluated_profiles.sort(key=lambda x: x['confidence'], reverse=True)

    best_profile = evaluated_profiles[0] if evaluated_profiles else None
    return best_profile, evaluated_profiles
