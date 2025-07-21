# backend/core/urls.py
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    FootImageUploadView,
    FootImageDetailView,
    get_csrf_token,
    signup,
    logout_view,
    user_info,
    shoe_list,
    shoe_detail,
    shoe_recommendations,
)

urlpatterns = [
    # CSRF
    path("csrf/", get_csrf_token, name="get-csrf-token"),

    # Auth
    path("auth/signup/", signup, name="signup"),
    path("auth/login/", obtain_auth_token, name="login"),
    path("auth/logout/", logout_view, name="logout"),
    path("auth/user/", user_info, name="user-info"),

    # Measurements
    path("measurements/upload/", FootImageUploadView.as_view(), name="measurement-upload"),
    path("measurements/<int:pk>/", FootImageDetailView.as_view(), name="measurement-detail"),
    
    # Shoes API
    path("shoes/", shoe_list, name="shoe-list"),
    path("shoes/<int:pk>/", shoe_detail, name="shoe-detail"),
    path("shoes/recommendations/", shoe_recommendations, name="shoe-recommendations"),
]