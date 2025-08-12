from django.db import models
from django.contrib.auth.models import User

class FootImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='foot_images', null=True, blank=True)  # Allow null for guests  
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
    area_sqin = models.FloatField(null=True, blank=True, help_text="Foot area in square inches")
    perimeter_inches = models.FloatField(null=True, blank=True, help_text="Foot perimeter in inches")
    error_message = models.TextField(null=True, blank=True)
    
    def __str__(self):
        if self.user:
            return f"FootImage {self.id} by {self.user.username}"
        elif self.error_message and self.error_message.startswith('GUEST_SESSION:'):
            session_id = self.error_message.replace('GUEST_SESSION:', '')[:8]
            return f"FootImage {self.id} by Guest ({session_id}...)"
        else:
            return f"FootImage {self.id} by Guest"


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
    
    # Basic shoe information
    company = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    us_size = models.DecimalField(max_digits=4, decimal_places=1)
    width_category = models.CharField(max_length=1, choices=WIDTH_CHOICES)
    function = models.CharField(max_length=20, choices=FUNCTION_CHOICES)
    price_usd = models.DecimalField(max_digits=8, decimal_places=2)
    product_url = models.URLField()
    is_active = models.BooleanField(default=True)
    
    # Store shoe image as URL
    shoe_image_url = models.URLField(
        null=True,
        blank=True,
        help_text="URL to the shoe product image (e.g., from manufacturer's website or CDN)"
    )
    
    # Insole processing fields 
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
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if this is a new image upload
        is_new_image = False
        if self.pk:
            try:
                old_instance = Shoe.objects.get(pk=self.pk)
                is_new_image = old_instance.insole_image != self.insole_image
            except Shoe.DoesNotExist:
                is_new_image = True
        else:
            is_new_image = bool(self.insole_image)
        
        # First, save the model to ensure the image file exists on disk
        super().save(*args, **kwargs)
        
        # THEN check if we need to process the image
        if self.insole_image and (not self.insole_length or is_new_image):
            logger.info(f"Processing insole image for shoe {self.id}", extra={
                'shoe_id': self.id,
                'has_image': bool(self.insole_image),
                'has_length': bool(self.insole_length),
                'is_new_image': is_new_image
            })
            
            try:
                # Import here to avoid circular imports
                from .views import process_insole_image_with_enhanced_measurements
                
                # Process the uploaded insole image (file now exists on disk)
                length, width, perimeter, area, error_msg = process_insole_image_with_enhanced_measurements(
                    self.insole_image.path
                )
                
                if not error_msg:
                    logger.info(f"Insole processing successful for shoe {self.id}", extra={
                        'shoe_id': self.id,
                        'length': length,
                        'width': width,
                        'perimeter': perimeter,
                        'area': area
                    })
                    
                    # Auto-populate the measurement fields
                    self.insole_length = length
                    self.insole_width = width
                    self.insole_perimeter = perimeter
                    self.insole_area = area
                    
                    # Save again with the measurements (without triggering infinite loop)
                    super().save(*args, **kwargs)
                else:
                    logger.error(f"Insole processing failed for shoe {self.id}", extra={
                        'shoe_id': self.id,
                        'error_message': error_msg
                    })
                    
            except Exception as e:
                logger.exception(f"Unexpected error processing insole for shoe {self.id}", extra={
                    'shoe_id': self.id,
                    'error': str(e)
                })
    
    def __str__(self):
        return f"{self.company} {self.model} (US {self.us_size})"
