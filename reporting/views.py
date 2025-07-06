from django.shortcuts import render, redirect
import os
import tempfile
from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML
from django.contrib import messages

def profile_result(request):
    result_data = request.session.get('result_data')
    if not result_data:
        messages.error(request, 'No result data found. Please upload a candidate profile first.')
        return redirect('upload_candidate')
    best_profile = result_data.get('best_profile', {})
    all_profiles_flat = result_data.get('all_profiles_flat', [])
    show_results = result_data.get('show_results', False)
    user_email = result_data.get('user_email', '')
    confidence_scores = result_data.get('confidence_scores', {})
    only_mock_data = result_data.get('only_mock_data', False)

    # Platform-specific mapping
    platform = best_profile.get('platform', '').lower()
    candidate_data = {
        'profile_picture': best_profile.get('profile_picture', ''),
        'full_name': best_profile.get('name', ''),
        'platform': best_profile.get('platform', ''),
        'handle': best_profile.get('handle', ''),
        'profile_url': best_profile.get('link', ''),
        'bio': best_profile.get('bio', ''),
        'education': best_profile.get('education', ''),
        'employment': best_profile.get('employment', ''),
        'skills': best_profile.get('skills', ''),
        'certifications': best_profile.get('certifications', ''),
        'summary': best_profile.get('summary', ''),
        'confidence_scores': confidence_scores,
        'all_profiles_flat': all_profiles_flat,
        'show_results': show_results,
        'user_email': user_email,
        'only_mock_data': only_mock_data,
        'contact': best_profile.get('contact', ''),
    }
    # LinkedIn: show connections, not followers/posts
    if platform == 'linkedin':
        # Try to extract connections from the bio or a dedicated field
        connections = ''
        bio = best_profile.get('bio', '')
        import re
        match = re.search(r'(\d{2,4}\+?)\s+connections', bio.lower())
        if match:
            connections = match.group(1) + ' connections'
        else:
            # fallback to a field if available
            connections = best_profile.get('connections', '')
        candidate_data['connections'] = connections or 'N/A'
        # Remove followers and posts for LinkedIn
        candidate_data['followers'] = ''
        candidate_data['posts'] = ''
    # Instagram: show followers and posts
    elif platform == 'instagram':
        candidate_data['followers'] = best_profile.get('followers', '')
        candidate_data['posts'] = best_profile.get('posts', '')
        candidate_data['connections'] = ''
    else:
        candidate_data['followers'] = best_profile.get('followers', '')
        candidate_data['posts'] = best_profile.get('posts', '')
        candidate_data['connections'] = ''
    return render(request, 'reporting/profile_result.html', candidate_data)

def download_pdf(request):
    result_data = request.session.get('result_data')
    if not result_data:
        messages.error(request, 'No result data found. Please upload a candidate profile first.')
        return redirect('upload_candidate')
    best_profile = result_data.get('best_profile', {})
    candidate_data = {
        'profile_picture': best_profile.get('profile_picture', ''),
        'full_name': best_profile.get('name', ''),
        'platform': best_profile.get('platform', ''),
        'handle': best_profile.get('handle', ''),
        'profile_url': best_profile.get('link', ''),
        'bio': best_profile.get('bio', ''),
        'education': best_profile.get('education', ''),
        'employment': best_profile.get('employment', ''),
        'followers': best_profile.get('followers', ''),
        'posts': best_profile.get('posts', ''),
        'contact': best_profile.get('contact', ''),
        'skills': best_profile.get('skills', ''),
        'certifications': best_profile.get('certifications', ''),
        'summary': best_profile.get('summary', ''),
        'confidence_scores': result_data.get('confidence_scores', {}),
    }
    template = get_template('reporting/profile_result.html')
    html_content = template.render(candidate_data)
    fd, path = tempfile.mkstemp(suffix='.pdf')
    os.close(fd)
    HTML(string=html_content).write_pdf(path)
    with open(path, 'rb') as f:
        pdf = f.read()
    os.remove(path)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Candidate_Report.pdf"'
    return response

