from django.urls import path
from . import views
from django.urls import path
from core.views import upload_candidate  # import your view

urlpatterns = [
    path('', views.upload_candidate, name='upload_candidate'),
    path('result/', views.show_result, name='show_result'),
    path('profile-results/', views.show_profile_results, name='profile_results'),
    path('social-results/', views.show_social_results, name='social_results'),
]
