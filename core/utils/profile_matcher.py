import re
from typing import Dict, Any, Tuple

import logging
from typing import Dict, Any, Tuple
from fuzzywuzzy import fuzz

def get_best_profile_match(user_input: Dict[str, Any], scraped_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Find the best matching profile from scraped data based on user input.
    Returns a detailed breakdown of matching criteria and overall score for each profile.
    
    Args:
        user_input: Dictionary containing user-provided data
        scraped_data: Dictionary containing scraped profile data
    
    Returns:
        Tuple containing:
            - Best matching profile with confidence score (or None if no match)
            - Dictionary of all scraped results with scores
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Get user-provided data
        user_name = user_input.get('full_name', '')
        user_email = user_input.get('email', '')
        user_position = user_input.get('position', '')
        user_company = user_input.get('company', '')
        user_name = user_name.lower() if isinstance(user_name, str) else ''
        user_email = user_email.lower() if isinstance(user_email, str) else ''
        user_position = user_position.lower() if isinstance(user_position, str) else ''
        user_company = user_company.lower() if isinstance(user_company, str) else ''
        
        # Initialize match variables
        best_profile = None
        best_score = 0
        all_profiles = []
        
        # Process LinkedIn profiles
        linkedin_profiles = scraped_data.get('linkedin_profiles', [])
        for profile in linkedin_profiles:
            try:
                # Criteria breakdown
                profile_name = profile.get('name', '')
                profile_name = profile_name.lower() if isinstance(profile_name, str) else ''
                name_match = fuzz.token_set_ratio(user_name, profile_name) if user_name else 0
                profile_email = profile.get('email', '')
                profile_email = profile_email.lower() if isinstance(profile_email, str) else ''
                email_match = fuzz.token_set_ratio(user_email, profile_email) if user_email and profile_email else 0
                profile_position = profile.get('position', '')
                profile_position = profile_position.lower() if isinstance(profile_position, str) else ''
                position_match = fuzz.token_set_ratio(user_position, profile_position) if user_position and profile_position else 0
                profile_company = profile.get('company', '')
                profile_company = profile_company.lower() if isinstance(profile_company, str) else ''
                company_match = fuzz.token_set_ratio(user_company, profile_company) if user_company and profile_company else 0
                # Weighted overall score
                overall = (
                    name_match * 0.5 +
                    email_match * 0.2 +
                    position_match * 0.15 +
                    company_match * 0.15
                )
                overall = min(100, round(overall, 2))
                # Ensure all fields are present
                enhanced_profile = {
                    'name': profile.get('name', 'N/A'),
                    'link': profile.get('link', '#'),
                    'confidence': overall,
                    'scores': {
                        'name_match': name_match,
                        'email_match': email_match,
                        'position_match': position_match,
                        'company_match': company_match,
                        'image_match': 0,
                        'metadata_correlation': 0,
                        'activity_level': 0,
                        'communication_style': 0,
                        'overall': overall
                    }
                }
                all_profiles.append(enhanced_profile)
                if overall > best_score:
                    best_score = overall
                    best_profile = enhanced_profile
            except Exception as e:
                logger.error(f'Error matching profile {profile.get("name", "Unknown")}: {str(e)}')
                continue
        # Process Instagram profiles
        instagram_profiles = scraped_data.get('instagram_profiles', [])
        all_instagram = []
        for profile in instagram_profiles:
            try:
                profile_name = profile.get('username', '')
                name_match = fuzz.token_set_ratio(user_name, profile_name) if user_name else 0
                # Instagram doesn't have email, position, company
                email_match = 0
                position_match = 0
                company_match = 0
                overall = name_match * 0.5  # Only name match for now
                overall = min(100, round(overall, 2))
                enhanced_profile = {
                    'name': profile.get('username', 'N/A'),
                    'link': profile.get('link', '#'),
                    'confidence': overall,
                    'scores': {
                        'name_match': name_match,
                        'email_match': email_match,
                        'position_match': position_match,
                        'company_match': company_match,
                        'image_match': 0,
                        'metadata_correlation': 0,
                        'activity_level': 0,
                        'communication_style': 0,
                        'overall': overall
                    }
                }
                all_instagram.append(enhanced_profile)
            except Exception as e:
                logger.error(f'Error matching Instagram profile {profile.get("username", "Unknown")}: {str(e)}')
                continue
        # Process YouTube profiles
        youtube_profiles = scraped_data.get('youtube_profiles', [])
        all_youtube = []
        for profile in youtube_profiles:
            try:
                profile_name = profile.get('title', '')
                name_match = fuzz.token_set_ratio(user_name, profile_name) if user_name else 0
                email_match = 0
                position_match = 0
                company_match = 0
                overall = name_match * 0.5
                overall = min(100, round(overall, 2))
                enhanced_profile = {
                    'name': profile.get('title', 'N/A'),
                    'link': profile.get('link', '#'),
                    'confidence': overall,
                    'scores': {
                        'name_match': name_match,
                        'email_match': email_match,
                        'position_match': position_match,
                        'company_match': company_match,
                        'image_match': 0,
                        'metadata_correlation': 0,
                        'activity_level': 0,
                        'communication_style': 0,
                        'overall': overall
                    }
                }
                all_youtube.append(enhanced_profile)
            except Exception as e:
                logger.error(f'Error matching YouTube profile {profile.get("title", "Unknown")}: {str(e)}')
                continue
        # Process Facebook profiles
        facebook_profiles = scraped_data.get('facebook_profiles', [])
        all_facebook = []
        for profile in facebook_profiles:
            try:
                profile_name = profile.get('name', '')
                name_match = fuzz.token_set_ratio(user_name, profile_name) if user_name else 0
                email_match = 0
                position_match = 0
                company_match = 0
                overall = name_match * 0.5
                overall = min(100, round(overall, 2))
                enhanced_profile = {
                    'name': profile.get('name', 'N/A'),
                    'link': profile.get('link', profile.get('url', '#')),
                    'confidence': overall,
                    'scores': {
                        'name_match': name_match,
                        'email_match': email_match,
                        'position_match': position_match,
                        'company_match': company_match,
                        'image_match': 0,
                        'metadata_correlation': 0,
                        'activity_level': 0,
                        'communication_style': 0,
                        'overall': overall
                    }
                }
                all_facebook.append(enhanced_profile)
            except Exception as e:
                logger.error(f'Error matching Facebook profile {profile.get("name", "Unknown")}: {str(e)}')
                continue
        # Sort all profiles by confidence
        all_profiles.sort(key=lambda x: x['confidence'], reverse=True)
        # Log results
        logger.info(f'Found {len(all_profiles)} profiles with best match confidence: {best_score}%')
        # Return best match and all results
        return best_profile, {
            'linkedin_profiles': all_profiles,
            'instagram_profiles': all_instagram,
            'youtube_profiles': all_youtube,
            'facebook_profiles': all_facebook
        }
        
    except Exception as e:
        logger.error(f'Error in get_best_profile_match: {str(e)}')
        return None, scraped_data
