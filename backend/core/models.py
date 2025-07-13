from django.db import models

class FootImage(models.Model):
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
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"FootImage {self.id}"


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

    company = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    us_size = models.DecimalField(max_digits=4, decimal_places=1)
    width_category = models.CharField(max_length=1, choices=WIDTH_CHOICES)
    function = models.CharField(max_length=100)
    price_usd = models.DecimalField(max_digits=8, decimal_places=2)
    product_url = models.URLField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.company} {self.model} (US {self.us_size})"
