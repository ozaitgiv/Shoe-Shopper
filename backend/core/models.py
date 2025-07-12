from django.db import models

class FootImage(models.Model):
    image = models.ImageField(upload_to='foot_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Simulated processing state
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('complete', 'Complete'),
        ('error', 'Error')
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='processing')
    length_inches = models.FloatField(null=True, blank=True)
    width_inches = models.FloatField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"FootImage {self.id}"
