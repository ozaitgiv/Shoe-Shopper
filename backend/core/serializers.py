from rest_framework import serializers
from .models import FootImage, Shoe

class FootImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FootImage
        fields = [
            'id', 'image', 'uploaded_at', 'status',
            'length_inches', 'width_inches', 'error_message'
        ]

class ShoeSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Shoe
        fields = [
            'id', 'company', 'model', 'gender', 'us_size', 
            'width_category', 'function', 'price_usd', 'product_url',
            'shoe_image_url', 'image_url', 'insole_length', 'insole_width',
            'insole_perimeter', 'insole_area', 'is_active'
        ]
    
    def get_image_url(self, obj):
        """Return the shoe image URL"""
        return obj.shoe_image_url