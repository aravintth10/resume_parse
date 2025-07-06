import os
import json
import serpapi
import requests
from bs4 import BeautifulSoup
from googlesearch import search
from youtube_search import YoutubeSearch
import logging
from typing import List, Dict, Optional
import time
import random
import re
from core.utils.platform_parsers import extract_linkedin_fields, extract_instagram_fields

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    # Add more user agents as needed
]

# Mock data for fallback
MOCK_LINKEDIN = [
    {"name": "Lakshanaa A", "link": "https://linkedin.com/in/lakshanaa", "snippet": "AI enthusiast, software developer", "confidence": 95}
]
MOCK_INSTAGRAM = [
    {"username": "lakshanaa_insta", "link": "https://instagram.com/lakshanaa", "bio": "AI | Dev | Blogger", "confidence": 80}
]
MOCK_YOUTUBE = [
    {"title": "Lakshanaa Channel", "link": "https://youtube.com/channel/UC123", "description": "Tech and AI videos", "confidence": 75}
]
MOCK_FACEBOOK = [
    {"name": "Lakshanaa A", "url": "https://facebook.com/lakshanaa", "snippet": "Works at Infosys", "confidence": 70}
]

def parse_linkedin_snippet(snippet, link) -> Dict[str, str]:
    # Use the new platform-specific parser
    parsed = extract_linkedin_fields(snippet)
    return {
        'bio': parsed['Bio'],
        'education': ', '.join(parsed['Education']) if isinstance(parsed['Education'], list) else parsed['Education'],
        'employment': ', '.join(parsed['Employment']) if isinstance(parsed['Employment'], list) else parsed['Employment'],
        'connections': parsed['Connections'],
        'skills': '',
        'certifications': '',
        'summary': '',
        'contact': link or '',
    }

def scrape_linkedin(name: str, email: Optional[str] = None) -> List[Dict[str, str]]:
    print("scrape_linkedin called")
    api_key = os.getenv("SERPAPI_API_KEY")
    logger.info(f"[DEBUG] Using SERPAPI_API_KEY: {api_key}")
    if not api_key:
        logger.error("SERPAPI_API_KEY not found in environment variables. Set your real SerpAPI key.")
        return [{
            "name": name,
            "link": f"https://linkedin.com/in/{name.lower().replace(' ', '')}",
            "snippet": f"This is a mock LinkedIn profile for {name}.",
            "bio": f"This is a mock LinkedIn profile for {name}.",
            "education": "",
            "employment": "",
            "followers": "",
            "skills": "",
            "contact": f"https://linkedin.com/in/{name.lower().replace(' ', '')}",
            "profile_picture": "N/A",
            "confidence": 50
        }]
    client = serpapi.Client(api_key=api_key)
    all_profiles = {}
    try:
        name_params = {"engine": "google", "q": f'"{name}" site:linkedin.com/in'}
        logger.info(f"Searching LinkedIn for name: {name}")
        results = client.search(name_params)
        logger.info(f"LinkedIn SerpAPI results: {results}")
        if "organic_results" in results:
            for result in results["organic_results"]:
                profile_link = result.get("link")
                snippet = result.get("snippet", "")
                # Parse snippet for more info
                parsed = parse_linkedin_snippet(snippet, profile_link)
                profile_picture = "N/A"
                try:
                    headers = {'User-Agent': random.choice(USER_AGENTS)}
                    resp = requests.get(profile_link, headers=headers, timeout=5)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        og_image = soup.find('meta', property='og:image')
                        if og_image and og_image.get('content'):
                            profile_picture = og_image['content']
                except Exception as e:
                    logger.warning(f"Could not fetch/parse LinkedIn profile page: {e}")
                profile = {
                    "name": result.get("title"),
                    "link": profile_link,
                    "snippet": snippet,
                    "bio": parsed['bio'],
                    "education": parsed['education'],
                    "employment": parsed['employment'],
                    "connections": parsed['connections'],
                    "profile_picture": profile_picture,
                    "source": "name_search"
                }
                logger.debug(f"Found LinkedIn profile: {profile}")
                all_profiles[profile_link] = profile
    except Exception as e:
        logger.error(f"Error in LinkedIn name search: {str(e)}")
        if '401' in str(e):
            logger.error("Unauthorized: Check your SerpAPI key.")
        if '429' in str(e):
            logger.error("Rate limited: Too many requests to SerpAPI.")
        return [{
            "name": name,
            "link": f"https://linkedin.com/in/{name.lower().replace(' ', '')}",
            "snippet": f"This is a mock LinkedIn profile for {name}.",
            "bio": f"This is a mock LinkedIn profile for {name}.",
            "education": "",
            "employment": "",
            "followers": "",
            "skills": "",
            "contact": f"https://linkedin.com/in/{name.lower().replace(' ', '')}",
            "profile_picture": "N/A",
            "confidence": 50
        }]
    for profile in all_profiles.values():
        profile["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        profile["confidence"] = 90 if "source" in profile else 80
        for field in ["bio", "education", "employment", "connections", "profile_picture"]:
            if field not in profile:
                profile[field] = ""
    logger.info(f"Found {len(all_profiles)} LinkedIn profiles")
    if all_profiles:
        return list(all_profiles.values())
    return [{
        "name": name,
        "link": f"https://linkedin.com/in/{name.lower().replace(' ', '')}",
        "snippet": f"This is a mock LinkedIn profile for {name}.",
        "bio": f"This is a mock LinkedIn profile for {name}.",
        "education": "",
        "employment": "",
        "followers": "",
        "skills": "",
        "contact": f"https://linkedin.com/in/{name.lower().replace(' ', '')}",
        "profile_picture": "N/A",
        "confidence": 50
    }]

def scrape_instagram(name: str, email: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Try to find Instagram profiles by searching Google for usernames, then fetch the public profile page directly.
    If all scraping fails, return a mock profile using the candidate's name.
    """
    profile_links = set()
    try:
        # Use Google search to find Instagram profile URLs
        name_query = f'"{name}" site:instagram.com'
        logger.info(f"Searching Instagram for name: {name}")
        for url in search(name_query, num_results=5):
            if "instagram.com" in url and '/p/' not in url:
                profile_links.add(url)
    except Exception as e:
        logger.error(f"Error in Instagram name search: {str(e)}")
        # Personalized fallback
        return [{"username": name.lower().replace(' ', '_'), "link": f"https://instagram.com/{name.lower().replace(' ', '')}", "bio": f"This is a mock Instagram bio for {name}.", "confidence": 50}]
    if email:
        try:
            email_query = f'"{email}" site:instagram.com'
            logger.info(f"Searching Instagram for email: {email}")
            for url in search(email_query, num_results=5):
                if "instagram.com" in url and '/p/' not in url:
                    profile_links.add(url)
        except Exception as e:
            logger.error(f"Error in Instagram email search: {str(e)}")
            # Personalized fallback
            return [{"username": name.lower().replace(' ', '_'), "link": f"https://instagram.com/{name.lower().replace(' ', '')}", "bio": f"This is a mock Instagram bio for {name}.", "confidence": 50}]
    profiles = []
    for link in profile_links:
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            time.sleep(random.uniform(1, 2))  # Shorter delay
            response = requests.get(link, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Instagram bio is in <meta property="og:description">
                description = soup.find("meta", property="og:description")
                bio = ""
                followers = posts = "N/A"
                profile_picture = "N/A"
                if description:
                    content = description["content"]
                    bio = content.split("•")[0].strip()
                    parts = content.split("•")
                    for part in parts:
                        if "Followers" in part:
                            followers = part.strip()
                        if "Posts" in part:
                            posts = part.strip()
                og_image = soup.find('meta', property='og:image')
                if og_image and og_image.get('content'):
                    profile_picture = og_image['content']
                username_match = re.search(r"instagram.com/([^/?#]+)", link)
                username = username_match.group(1) if username_match else ''
                # Skip if the page is a login page or blocked
                if "login" in response.url or (soup.title and "Log in" in soup.title.string):
                    logger.info(f"Skipped login-blocked Instagram page: {link}")
                    continue
                parsed = extract_instagram_fields(bio)
                profile = {
                    "username": username,
                    "link": link,
                    "followers": parsed['Followers'],
                    "posts": parsed['Posts'],
                    "bio": bio,
                    "profile_picture": profile_picture,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "confidence": 70
                }
                # Ensure all fields are present
                for field in ["username", "followers", "posts", "bio", "profile_picture"]:
                    if field not in profile:
                        profile[field] = "N/A"
                profiles.append(profile)
            else:
                logger.warning(f"Failed to fetch Instagram profile {link}: Status {response.status_code}")
        except Exception as e:
            logger.error(f"Error scraping Instagram profile {link}: {str(e)}")
            continue
    logger.info(f"Found {len(profiles)} Instagram profiles")
    if profiles:
        return profiles
    # Personalized fallback if no profiles found
    return [{"username": name.lower().replace(' ', '_'), "link": f"https://instagram.com/{name.lower().replace(' ', '')}", "bio": f"This is a mock Instagram bio for {name}.", "confidence": 50}]

def scrape_youtube(name: str, email: Optional[str] = None) -> List[Dict[str, str]]:
    search_terms = [f'"{name}"']
    if email:
        search_terms.append(f'"{email}"')
    all_channels = {}
    for term in search_terms:
        try:
            logger.info(f"Searching YouTube for term: {term}")
            # Try YoutubeSearch library first
            try:
                results_json = YoutubeSearch(term, max_results=5).to_json()
                results = json.loads(results_json)
                for channel in results.get('channels', []):
                    channel_id = channel.get('channelId')
                    if channel_id:
                        # Try to fetch channel page for more info
                        description = channel.get('description', '')
                        subscribers = videos = "N/A"
                        profile_picture = "N/A"
                        try:
                            channel_url = f"https://www.youtube.com/channel/{channel_id}"
                            headers = {'User-Agent': random.choice(USER_AGENTS)}
                            resp = requests.get(channel_url, headers=headers, timeout=5)
                            if resp.status_code == 200:
                                soup = BeautifulSoup(resp.text, 'html.parser')
                                # Subscribers
                                sub_tag = soup.find('yt-formatted-string', {'id': 'subscriber-count'})
                                if sub_tag:
                                    subscribers = sub_tag.get_text(strip=True)
                                # Videos: Not reliably available, set to N/A
                                og_image = soup.find('meta', property='og:image')
                                if og_image and og_image.get('content'):
                                    profile_picture = og_image['content']
                        except Exception as e:
                            logger.warning(f"Could not fetch/parse YouTube channel page: {e}")
                        channel_data = {
                            "title": channel.get('title', ''),
                            "link": channel_url,
                            "description": description,
                            "followers": subscribers,
                            "posts": videos,
                            "profile_picture": profile_picture,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "confidence": 80
                        }
                        # Ensure all fields are present
                        for field in ["description", "followers", "posts", "profile_picture"]:
                            if field not in channel_data:
                                channel_data[field] = "N/A"
                        logger.debug(f"Found YouTube channel: {channel_data}")
                        all_channels[channel_id] = channel_data
            except Exception as e:
                logger.warning(f"YoutubeSearch failed, falling back to HTML scraping: {e}")
                # Fallback: scrape YouTube search results page
                query = term.replace('"', '')
                url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        if '/channel/' in a['href']:
                            channel_id = a['href'].split('/channel/')[-1].split('/')[0]
                            title = a.get('title', '') or a.text.strip()
                            link = f"https://youtube.com/channel/{channel_id}"
                            if channel_id not in all_channels:
                                all_channels[channel_id] = {"title": title, "link": link, "description": '', "followers": "N/A", "posts": "N/A", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "profile_picture": "N/A", "confidence": 70}
                else:
                    logger.warning(f"Failed to fetch YouTube search page: Status {response.status_code}")
        except Exception as e:
            logger.error(f"Error in YouTube search for term '{term}': {str(e)}")
            continue
    logger.info(f"Found {len(all_channels)} YouTube channels")
    if all_channels:
        return list(all_channels.values())
    # Personalized fallback if no channels found
    return [{"title": f"{name} Channel", "link": f"https://youtube.com/@{name.lower().replace(' ', '')}", "description": f"This is a mock YouTube channel for {name}.", "followers": "N/A", "posts": "N/A", "profile_picture": "N/A", "confidence": 50}]

def scrape_facebook(name, email=None):
    profile_links = set()
    try:
        name_query = f'"{name}" site:facebook.com'
        for url in search(name_query, num_results=5):
            if "facebook.com" in url and '/posts/' not in url and '/groups/' not in url:
                profile_links.add(url)
    except Exception as e:
        logger.error(f"Error during Facebook name search: {str(e)}")
        return [{"name": name, "url": f"https://facebook.com/{name.lower().replace(' ', '')}", "description": f"This is a mock Facebook profile for {name}.", "bio": "N/A", "employment": "N/A", "education": "N/A", "followers": "N/A", "posts": "N/A", "profile_picture": "N/A", "confidence": 50}]
    if email:
        try:
            email_query = f'"{email}" site:facebook.com'
            for url in search(email_query, num_results=5):
                if "facebook.com" in url and '/posts/' not in url and '/groups/' not in url:
                    profile_links.add(url)
        except Exception as e:
            logger.error(f"Error during Facebook email search: {str(e)}")
            return [{"name": name, "url": f"https://facebook.com/{name.lower().replace(' ', '')}", "description": f"This is a mock Facebook profile for {name}.", "bio": "N/A", "employment": "N/A", "education": "N/A", "followers": "N/A", "posts": "N/A", "profile_picture": "N/A", "confidence": 50}]
    profiles = []
    for url in profile_links:
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            time.sleep(random.uniform(1, 2))
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.title.string if soup.title else "No title found"
                # Skip login or sign up pages
                if "log in" in title.lower() or "sign up" in title.lower():
                    logger.info(f"Skipped login-blocked Facebook page: {url}")
                    continue
                # Try to extract public info
                description = ""
                desc_tag = soup.find("meta", property="og:description")
                if desc_tag:
                    description = desc_tag.get("content", "")
                # Try to extract employment/education/followers from description or visible text
                employment = education = followers = posts = "N/A"
                profile_picture = "N/A"
                if description:
                    # Heuristic: look for keywords
                    if "Works at" in description:
                        employment = description.split("Works at")[-1].split(".")[0].strip()
                    if "Studied at" in description:
                        education = description.split("Studied at")[-1].split(".")[0].strip()
                    follower_match = re.search(r'(\d+[,.]?\d*) followers', description)
                    if follower_match:
                        followers = follower_match.group(1)
                og_image = soup.find('meta', property='og:image')
                if og_image and og_image.get('content'):
                    profile_picture = og_image['content']
                profiles.append({
                    'url': url,
                    'title': title,
                    'description': description or f"Found a potential Facebook profile. Direct scraping is blocked.",
                    'bio': description,
                    'employment': employment,
                    'education': education,
                    'followers': followers,
                    'posts': posts,
                    'profile_picture': profile_picture,
                    'confidence': 60
                })
            else:
                logger.warning(f"Failed to fetch Facebook profile {url}: Status {response.status_code}")
        except Exception as e:
            logger.error(f"Error scraping Facebook URL {url}: {str(e)}")
            continue
    logger.info(f"Found {len(profiles)} Facebook profiles")
    if profiles:
        return profiles
    return [{"name": name, "url": f"https://facebook.com/{name.lower().replace(' ', '')}", "description": f"This is a mock Facebook profile for {name}.", "bio": "N/A", "employment": "N/A", "education": "N/A", "followers": "N/A", "posts": "N/A", "profile_picture": "N/A", "confidence": 50}]
