'''
from django.urls import path
from .views import FootImageUploadView, upload_form_view

urlpatterns = [
    path('upload/', FootImageUploadView.as_view(), name='image-upload'),
    path('upload-form/', upload_form_view, name='upload-form'),  # for testing
]
'''
# UPDATED URLS

from django.urls import path
from .views import FootImageUploadView
from accounts.views import RegisterView, LoginView, LogoutView

urlpatterns = [
    path('upload/', FootImageUploadView.as_view(), name='image-upload'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
