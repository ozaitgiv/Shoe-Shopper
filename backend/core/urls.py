from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    FootImageUploadView,
    FootImageDetailView,
    get_latest_measurement,  
    get_csrf_token,
    signup,
    logout_view,
    user_info,
    recommendations,
    delete_account,
)

urlpatterns = [
    # CSRF
    path("csrf/", get_csrf_token, name="get-csrf-token"),

    # Auth
    path("auth/signup/", signup, name="signup"),
    path("auth/login/", obtain_auth_token, name="login"),
    path("auth/logout/", logout_view, name="logout"),
    path("auth/user/", user_info, name="user-info"),
    path("auth/account/", delete_account, name="delete-account"),

    # Measurements
    path("measurements/upload/", FootImageUploadView.as_view(), name="measurement-upload"),
    path("measurements/<int:pk>/", FootImageDetailView.as_view(), name="measurement-detail"),
    path("recommendations/", recommendations, name="recommendations"),
    path("measurements/latest/", get_latest_measurement, name="latest-measurement"),  
]
