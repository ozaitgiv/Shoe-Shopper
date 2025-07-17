from django.db import models
from django.contrib.auth.models import User

class FootImage(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='foot_images')
    
    image = models.ImageField(upload_to='foot_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('complete', 'Complete'),
        ('error', 'Error'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='processing')
    length_inches = models.FloatField(null=True, blank=True)
    width_inches = models.FloatField(null=True, blank=True)
    perimeter_inches = models.FloatField(null=True, blank=True, help_text="Perimeter in inches")
    area_sq_inches = models.FloatField(null=True, blank=True, help_text="Area in square inches")
    error_message = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"FootImage {self.id} - {self.user.username}"


class Shoe(models.Model):
    GENDER_CHOICES = [
        ('M', 'Men'),
        ('W', 'Women'),
        ('U', 'Unisex'),
    ]
    
    WIDTH_CHOICES = [
        ('N', 'Narrow'),
        ('D', 'Regular'),
        ('W', 'Wide'),
    ]
    
    FUNCTION_CHOICES = [
        ('casual', 'Casual'),
        ('hiking', 'Hiking'),
        ('work', 'Work'),
        ('running', 'Running'),
    ]
    
    company = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    us_size = models.DecimalField(max_digits=4, decimal_places=1)
    width_category = models.CharField(max_length=1, choices=WIDTH_CHOICES)
    function = models.CharField(max_length=20, choices=FUNCTION_CHOICES)
    price_usd = models.DecimalField(max_digits=8, decimal_places=2)
    product_url = models.URLField()
    is_active = models.BooleanField(default=True)
    
    insole_image = models.ImageField(
        upload_to='insole_images/',
        null=True,
        blank=True,
        help_text="Upload insole photo to automatically calculate measurements"
    )
    insole_length = models.FloatField(null=True, blank=True, help_text="Length in inches")
    insole_width = models.FloatField(null=True, blank=True, help_text="Width in inches")
    insole_perimeter = models.FloatField(null=True, blank=True, help_text="Perimeter in inches")
    insole_area = models.FloatField(null=True, blank=True, help_text="Area in square inches")
    
    def save(self, *args, **kwargs):
        """Override save to auto-process insole image when uploaded"""

        super().save(*args, **kwargs)
        
        if self.insole_image and not self.insole_length:
            try:

                from .views import process_insole_image_with_enhanced_measurements
                
                length, width, perimeter, area, error_msg = process_insole_image_with_enhanced_measurements(
                    self.insole_image.path
                )
                
                if not error_msg:
                    self.insole_length = length
                    self.insole_width = width
                    self.insole_perimeter = perimeter
                    self.insole_area = area
                    
                    super().save(*args, **kwargs)
                    
            except Exception as e:
                pass

    def __str__(self):
        return f"{self.company} {self.model} (US {self.us_size})"