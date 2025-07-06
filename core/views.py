from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.core.files.storage import FileSystemStorage
from django.template.loader import get_template
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib import messages
import logging
from .forms import CandidateForm
from .utils.resume_parser import parse_resume
from .utils.social_scraper import scrape_linkedin, scrape_instagram, scrape_youtube, scrape_facebook
from .utils.profile_matcher import get_best_profile_match
import pdfkit
import os
import traceback
from core.utils.linkedin_profile_parser import extract_profile_fields
from core.utils.platform_parsers import extract_linkedin_fields, extract_instagram_fields

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

WKHTMLTOPDF_PATH = r'C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe'  # Update this path if needed

# Sample scraped bios - replace this with dynamic data later
scraped_bios = [
    "Mukeshwaran s. Associate at Acuity knowledge partners. Acuity Knowledge Partners SRM University. Chennai. 856 followers.",
    "Mukeshwaran P. Area Sales Manager @ One97 communications limited. One97 Communications Limited karunya University. Chennai. 307 followers.",
    "MUKESHWARAN D. Netcore Cloud KGiSL Institute of Technology. Coimbatore. 48 followers."
]

# Example scraped texts per platform
linkedin_data = [
    "Mukeshwaran s. Associate at Acuity knowledge partners. SRM University. 856 followers.",
    "Mukeshwaran P. Area Sales Manager @ One97. Karunya University. 307 connections."
]
instagram_data = [
    "Mukesh_23 | 2.1k followers | 54 posts",
    "d.mukesh__ | 865 followers | 38 posts"
]

def upload_candidate(request):
    print("upload_candidate view called")  # Debug: view is called
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Get form data
                manual_data = form.cleaned_data
                
                # Get user email
                user_email = manual_data.get('user_email')
                if not user_email:
                    messages.error(request, 'Please provide a valid email address')
                    return render(request, 'core/form_upload.html', {'form': form})

                # Resume parsing
                parsed_data = {}
                resume_file = request.FILES.get('resume')
                if resume_file:
                    try:
                        fs = FileSystemStorage()
                        filename = fs.save(resume_file.name, resume_file)
                        filepath = fs.path(filename)
                        parsed_data = parse_resume(filepath)
                        fs.delete(filename)
                    except Exception as e:
                        logger.error(f'Resume parsing failed: {str(e)}')
                        messages.warning(request, 'Failed to parse resume')

                # Get name and email for scraping
                full_name = parsed_data.get('full_name') or manual_data.get('full_name')
                email = parsed_data.get('email')[0] if parsed_data.get('email') else manual_data.get('email')

                # Always use resume name for scraping if available
                scrape_name = parsed_data.get('full_name') or manual_data.get('full_name')
                scrape_email = parsed_data.get('email')[0] if parsed_data.get('email') else manual_data.get('email')

                # Scrape profiles
                print("About to call scrape_linkedin")  # Debug: before scraping
                linkedin_profiles_raw = scrape_linkedin(scrape_name, scrape_email) or []
                instagram_profiles_raw = scrape_instagram(scrape_name, scrape_email) or []
                youtube_profiles = scrape_youtube(scrape_name, scrape_email) or []
                facebook_profiles = scrape_facebook(scrape_name, scrape_email) or []
                # Detect if mock data is used (by checking for known mock names/links)
                used_mock_data = False
                if (linkedin_profiles_raw and linkedin_profiles_raw[0].get('name', '').startswith('Lakshanaa')) or \
                   (instagram_profiles_raw and instagram_profiles_raw[0].get('username', '').startswith('lakshanaa')):
                    used_mock_data = True

                # Only show results if any real data is found
                if linkedin_profiles_raw or instagram_profiles_raw or youtube_profiles or facebook_profiles:
                    show_results = True
                else:
                    show_results = False
                    messages.warning(request, 'No real profiles found for this candidate. Displaying no results.')

                # Parse LinkedIn profiles for clean, platform-specific fields
                linkedin_profiles = []
                for profile in linkedin_profiles_raw:
                    parsed = extract_linkedin_fields(profile.get('snippet', ''))
                    linkedin_profiles.append({
                        'name': profile.get('name', 'N/A'),
                        'link': profile.get('link', '#'),
                        'bio': parsed.get('Bio', 'N/A'),
                        'education': ', '.join(parsed.get('Education', [])),
                        'employment': ', '.join(parsed.get('Employment', [])),
                        'connections': parsed.get('Connections', 'N/A'),
                    })

                # Parse Instagram profiles for clean, platform-specific fields
                instagram_profiles = []
                for profile in instagram_profiles_raw:
                    parsed = extract_instagram_fields(profile.get('bio', ''))
                    instagram_profiles.append({
                        'link': profile.get('link', '#'),
                        'followers': parsed.get('Followers', 'N/A'),
                        'posts': parsed.get('Posts', 'N/A'),
                    })

                # Format scraped data for display
                scraped_data = {
                    'linkedin_profiles': linkedin_profiles,
                    'instagram_profiles': instagram_profiles,
                    'youtube_profiles': [
                        {
                            'platform': 'YouTube',
                            'handle': profile.get('title', 'N/A'),
                            'url': profile.get('link', '#'),
                            'score': f"{profile.get('confidence', 0)}%",
                            'details': profile.get('description', '')
                        } for profile in youtube_profiles
                    ],
                    'facebook_profiles': [
                        {
                            'platform': 'Facebook',
                            'handle': profile.get('name', 'N/A'),
                            'url': profile.get('link', '#'),
                            'score': f"{profile.get('confidence', 0)}%",
                            'details': profile.get('snippet', '')
                        } for profile in facebook_profiles
                    ]
                }

                # Prepare user input for profile matching
                user_input = {
                    'full_name': full_name,
                    'email': parsed_data.get('email', [None])[0] or manual_data.get('email'),
                    'linkedin': parsed_data.get('linkedin', '') or manual_data.get('linkedin', ''),
                    'github': parsed_data.get('github', '') or manual_data.get('github', ''),
                    'position': parsed_data.get('position', '') or manual_data.get('position', ''),
                    'company': parsed_data.get('company', '') or manual_data.get('company', ''),
                }

                # Pass raw profiles to matcher
                raw_scraped_data = {
                    'linkedin_profiles': linkedin_profiles_raw,
                    'instagram_profiles': instagram_profiles_raw,
                    'youtube_profiles': youtube_profiles,
                    'facebook_profiles': facebook_profiles,
                }
                best_profile, all_results = get_best_profile_match(user_input, raw_scraped_data)

                # Generate PDF
                pdf_template = get_template('core/pdf_template.html')
                pdf_content = pdf_template.render({
                    'manual_data': manual_data,
                    'parsed_data': parsed_data,
                    'linkedin_profiles': linkedin_profiles,
                    'instagram_profiles': instagram_profiles,
                    'youtube_profiles': youtube_profiles,
                    'facebook_profiles': facebook_profiles,
                    'best_profile': best_profile,
                    'all_profiles': all_results,
                    'final_score': best_profile['confidence'] if best_profile else 0,
                })

                try:
                    config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
                    pdf_file = pdfkit.from_string(pdf_content, False, configuration=config)
                except Exception as pdf_err:
                    logger.error(f'PDF generation failed: {pdf_err}')
                    messages.error(request, 'PDF generation failed. Please check wkhtmltopdf installation.')
                    return render(request, 'core/form_upload.html', {'form': form})

                pdf_path = os.path.join(settings.MEDIA_ROOT, 'reports', f'report_{user_email.replace("@", "_")}.pdf')
                os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_file)

                # Send email with PDF attachment
                email = EmailMessage(
                    'Profile Analysis Report',
                    'Please find your profile analysis report attached.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user_email]
                )
                email.attach_file(pdf_path)
                email.send()

                # Prepare confidence scores for template
                confidence_scores = best_profile.get('scores', {}) if best_profile and 'scores' in best_profile else {
                    'overall': best_profile['confidence'] if best_profile else 0,
                    'name_match': 0,
                    'image_match': 0,
                    'metadata_correlation': 0,
                    'activity_level': 0,
                    'communication_style': 0
                }
                
                # To prevent errors when storing form data in the session, we create a 
                # serializable dictionary that excludes any uploaded file objects.
                manual_data_serializable = {
                    key: value for key, value in manual_data.items() 
                    if not hasattr(value, 'read')
                }

                # Debug: print what is being passed to the template
                print("linkedin_profiles to template:", linkedin_profiles)

                # Prepare a flat list of all profiles for the table
                all_profiles_flat = []
                for platform_key, platform_name, handle_key in [
                    ('linkedin_profiles', 'LinkedIn', 'name'),
                    ('instagram_profiles', 'Instagram', 'username'),
                    ('youtube_profiles', 'YouTube', 'title'),
                    ('facebook_profiles', 'Facebook', 'name'),
                ]:
                    for profile in all_results.get(platform_key, []):
                        all_profiles_flat.append({
                            'platform': platform_name,
                            'handle': profile.get(handle_key, 'N/A'),
                            'link': profile.get('link', profile.get('url', '#')),
                            'scores': profile.get('scores', {}),
                            'confidence': profile.get('confidence', 0),
                            'bio': profile.get('bio', profile.get('snippet', 'N/A')),
                            'education': profile.get('education', 'N/A'),
                            'employment': profile.get('employment', 'N/A'),
                            'followers': profile.get('followers', 'N/A'),
                            'posts': profile.get('posts', 'N/A'),
                        })

                # If best_profile exists, enrich it with platform, handle, and new fields from all_profiles_flat
                if best_profile:
                    for p in all_profiles_flat:
                        if (
                            p.get('link') == best_profile.get('link') and
                            abs(p.get('confidence', 0) - best_profile.get('confidence', 0)) < 0.01
                        ):
                            best_profile['platform'] = p.get('platform', 'N/A')
                            best_profile['handle'] = p.get('handle', 'N/A')
                            best_profile['bio'] = p.get('bio', 'N/A')
                            best_profile['education'] = p.get('education', 'N/A')
                            best_profile['employment'] = p.get('employment', 'N/A')
                            best_profile['followers'] = p.get('followers', 'N/A')
                            best_profile['posts'] = p.get('posts', 'N/A')
                            break

                # Store result data in session to pass to the result page
                request.session['result_data'] = {
                    'manual_data': manual_data_serializable,
                    'parsed_data': parsed_data,
                    'linkedin_profiles': linkedin_profiles,  # Now parsed and clean
                    'instagram_profiles': instagram_profiles,
                    'youtube_profiles': youtube_profiles,
                    'facebook_profiles': facebook_profiles,
                    'best_profile': best_profile,
                    'all_profiles': all_results,
                    'all_profiles_flat': all_profiles_flat,
                    'final_score': best_profile['confidence'] if best_profile else 0,
                    'user_email': user_email,
                    'pdf_path': f'/media/reports/report_{user_email.replace("@", "_")}.pdf',
                    'confidence_scores': confidence_scores,
                    'show_results': show_results
                }

                # Redirect to the result page to avoid form resubmission on refresh
                return redirect('show_result')

            except Exception as e:
                logger.error(f'Error in upload_candidate: {str(e)}\n{traceback.format_exc()}')
                messages.error(request, 'An error occurred while processing your request')
                return render(request, 'core/form_upload.html', {'form': form})
    else:
        form = CandidateForm()
        return render(request, 'core/form_upload.html', {'form': form})

def show_result(request):
    """
    Displays the result page by fetching data from the session.
    This prevents form resubmission on page refresh.
    """
    result_data = request.session.get('result_data')

    if not result_data:
        # If no data, redirect to the upload form
        messages.warning(request, "No result data found. Please submit the form again.")
        return redirect('upload_candidate')

    # Add data_sources for parsed resume fields
    parsed_data = result_data.get('parsed_data', {})
    data_sources = {}
    for field in ['full_name', 'email', 'phone', 'linkedin', 'github']:
        if parsed_data.get(field):
            data_sources[field] = 'resume'
        else:
            data_sources[field] = ''
    result_data['data_sources'] = data_sources

    # By rendering the data here, refreshing the /result/ page will not
    # trigger a form resubmission warning in the browser.
    return render(request, 'core/result.html', result_data)

def show_profile_results(request):
    parsed_results = []
    for bio in scraped_bios:
        result = extract_profile_fields(bio)
        parsed_results.append(result)
    return render(request, 'profile_results.html', {'results': parsed_results})

def show_social_results(request):
    linkedin_results = [extract_linkedin_fields(text) for text in linkedin_data]
    instagram_results = [extract_instagram_fields(text) for text in instagram_data]
    context = {
        'linkedin_results': linkedin_results,
        'instagram_results': instagram_results
    }
    return render(request, 'social_results.html', context)
