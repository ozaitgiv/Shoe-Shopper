from django.db import models

# Create your models here.

# For image uploads
class FootImage(models.Model):
    image = models.ImageField(upload_to='foot_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

