from difflib import SequenceMatcher

def calculate_name_similarity(name1, name2):
    """Calculate similarity between two names."""
    if not name1 or not name2:
        return 0
    return SequenceMatcher(None, str(name1).lower(), str(name2).lower()).ratio() * 100

def calculate_profile_confidence(user_input, profile):
    """
    Calculate a detailed confidence score breakdown for a single profile.
    Returns the final score and a dictionary of score components.
    """
    scores = {
        'name_match': 0,
        'metadata_correlation': 0,
        'image_match': 0,  # Placeholder for future implementation
        'activity_level': 0, # Placeholder for future implementation
    }
    
    # --- Golden Signal Checks (very high confidence) ---
    # 1. Exact email match in description
    if 'email' in user_input and user_input.get('email'):
        if 'description' in profile and profile.get('description') and user_input['email'].lower() in str(profile['description']).lower():
            scores['name_match'] = calculate_name_similarity(user_input.get('full_name'), profile.get('name'))
            scores['metadata_correlation'] = 100
            scores['overall'] = 95
            return scores['overall'], scores

    # 2. Exact LinkedIn URL match
    if 'linkedin' in user_input and user_input.get('linkedin'):
        if 'url' in profile and profile.get('url') and str(user_input['linkedin']).lower() == str(profile['url']).lower():
            scores['name_match'] = calculate_name_similarity(user_input.get('full_name'), profile.get('name'))
            scores['metadata_correlation'] = 100
            scores['overall'] = 95
            return scores['overall'], scores

    # --- Standard Fallback Logic ---
    # Name Match
    if 'full_name' in user_input and user_input.get('full_name'):
        scores['name_match'] = round(calculate_name_similarity(user_input['full_name'], profile.get('name', '')))

    # Metadata Correlation
    meta_score = 0
    meta_factors = 0
    # URL matching
    if 'linkedin' in user_input and user_input.get('linkedin') and 'url' in profile and profile.get('url'):
        meta_score += 100 if str(user_input['linkedin']).lower() == str(profile['url']).lower() else 0
        meta_factors += 1
    # Content matching
    if 'description' in profile and profile.get('description') and 'full_name' in user_input and user_input.get('full_name'):
        meta_score += 100 if str(user_input['full_name']).lower() in str(profile['description']).lower() else 0
        meta_factors += 1
    # Email matching
    if 'description' in profile and profile.get('description') and 'email' in user_input and user_input.get('email'):
        meta_score += 100 if user_input['email'].lower() in str(profile['description']).lower() else 0
        meta_factors += 1
    scores['metadata_correlation'] = round(meta_score / meta_factors) if meta_factors > 0 else 0

    # Calculate Overall Score (weighted average)
    overall_score = (scores['name_match'] * 0.7) + (scores['metadata_correlation'] * 0.3)
    scores['overall'] = round(overall_score)

    return scores['overall'], scores

def get_best_profile_match(user_input, scraped_profiles):
    """
    Compare all scraped profiles against user input and return the best match
    along with all comparison results.
    """
    all_results = []
    
    # Process LinkedIn profiles
    for profile in scraped_profiles.get('linkedin', []):
        confidence, detailed_scores = calculate_profile_confidence(user_input, {
            'name': profile.get('name', ''),
            'description': profile.get('snippet', ''),
            'url': profile.get('link', '')
        })
        all_results.append({
            'platform': 'LinkedIn',
            'handle': profile.get('name', 'Unknown'),
            'url': profile.get('link', ''),
            'confidence': confidence,
            'scores': detailed_scores
        })

    # Process Instagram profiles
    for profile in scraped_profiles.get('instagram', []):
        bio = profile.get('bio', '')
        name = bio.split('\n')[0] if bio else ''
        confidence, detailed_scores = calculate_profile_confidence(user_input, {
            'name': name,
            'description': bio,
            'url': profile.get('link', '')
        })
        all_results.append({
            'platform': 'Instagram',
            'handle': profile.get('link', '').split('/')[-1] if profile.get('link') else 'Unknown',
            'url': profile.get('link', ''),
            'confidence': confidence,
            'scores': detailed_scores
        })

    # Process Facebook profiles
    for profile in scraped_profiles.get('facebook', []):
        confidence, detailed_scores = calculate_profile_confidence(user_input, {
            'name': profile.get('title', ''),
            'description': profile.get('description', ''),
            'url': profile.get('url', '')
        })
        all_results.append({
            'platform': 'Facebook',
            'handle': profile.get('title', 'Unknown'),
            'url': profile.get('url', ''),
            'confidence': confidence,
            'scores': detailed_scores
        })

    # Process YouTube profiles
    for profile in scraped_profiles.get('youtube', []):
        confidence, detailed_scores = calculate_profile_confidence(user_input, {
            'name': profile.get('channel', ''),
            'description': profile.get('description', ''),
            'url': profile.get('link', '')
        })
        all_results.append({
            'platform': 'YouTube',
            'handle': profile.get('channel', 'Unknown'),
            'url': profile.get('link', ''),
            'confidence': confidence,
            'scores': detailed_scores
        })

    # Sort results by confidence score
    all_results.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Return the best match and all results
    best_profile = all_results[0] if all_results else None
    return best_profile, all_results 