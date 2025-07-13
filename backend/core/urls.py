from django.urls import path
from .views import FootImageUploadView, upload_form_view

urlpatterns = [
    path('upload/', FootImageUploadView.as_view(), name='image-upload'),
    path('upload-form/', upload_form_view, name='upload-form'),  # for testing
]

