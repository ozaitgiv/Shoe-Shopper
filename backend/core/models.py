from django.db import models
from django.contrib.auth.models import User

# Create your models here.

'''
# For image uploads
class FootImage(models.Model):
    image = models.ImageField(upload_to='foot_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

'''


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ShoeCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Shoe(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    category = models.ForeignKey(ShoeCategory, on_delete=models.CASCADE)
    model_name = models.CharField(max_length=200)
    style_code = models.CharField(max_length=50, blank=True)
    price_range = models.CharField(max_length=20, blank=True)
    availability_status = models.CharField(max_length=20, default='available')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand.name} {self.model_name}"

class ShoeMeasurement(models.Model):
    shoe = models.ForeignKey(Shoe, on_delete=models.CASCADE, related_name='measurements')
    size_us = models.DecimalField(max_digits=3, decimal_places=1)
    size_eu = models.IntegerField(null=True, blank=True)
    length_mm = models.DecimalField(max_digits=5, decimal_places=2)
    width_mm = models.DecimalField(max_digits=5, decimal_places=2)
    arch_height_mm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    measurement_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.shoe} - Size {self.size_us}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class FootMeasurement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    foot_length_mm = models.DecimalField(max_digits=5, decimal_places=2)
    foot_width_mm = models.DecimalField(max_digits=5, decimal_places=2)
    arch_height_mm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    measurement_confidence = models.DecimalField(max_digits=3, decimal_places=2, default=0.8)
    measurement_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.measurement_date.date()}"

# ----------------- Existing FootImage Function Retained----- Added Relationships

# Added fucntionality to track processing status and/or erros during image analysis

class FootImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='foot_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processing_status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ]
    )
    error_message = models.TextField(null=True, blank=True)

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    foot_measurement = models.ForeignKey(FootMeasurement, on_delete=models.CASCADE)
    shoe = models.ForeignKey(Shoe, on_delete=models.CASCADE)
    recommended_size_us = models.DecimalField(max_digits=3, decimal_places=1)
    similarity_score = models.DecimalField(max_digits=5, decimal_places=4)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2)
    recommendation_date = models.DateTimeField(auto_now_add=True)
    user_feedback = models.IntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])
    
    def __str__(self):
        return f"{self.user.username} - {self.shoe} - Size {self.recommended_size_us}"