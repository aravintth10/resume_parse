from django.urls import path
from . import views
from django.urls import path
from core.views import upload_candidate  # import your view

urlpatterns = [
    path('', upload_candidate, name='home'),  # Home page URL
    # ... other URLs ...
]




urlpatterns = [
    path('result/', views.profile_result, name='profile_result'),
    path('download/', views.download_pdf, name='download_pdf'),  # <--- new line
]
