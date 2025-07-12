from django.urls import path
from .views import FootImageUploadView, FootImageDetailView, get_csrf_token

urlpatterns = [
    path("measurements/upload/", FootImageUploadView.as_view(), name="measurement-upload"),
    path("measurements/<int:pk>/", FootImageDetailView.as_view(), name="measurement-detail"),
    path("csrf/", get_csrf_token, name="get-csrf-token"),  # CSRF token endpoint
]
