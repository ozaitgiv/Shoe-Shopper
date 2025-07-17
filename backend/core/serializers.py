from rest_framework import serializers
from .models import FootImage

class FootImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FootImage
        fields = [
            'id', 'image', 'uploaded_at', 'status',
            'length_inches', 'width_inches', 
            'perimeter_inches', 'area_sq_inches',
            'error_message'
        ]
        read_only_fields = [
            'uploaded_at', 'status', 'length_inches', 'width_inches', 
            'perimeter_inches', 'area_sq_inches', 'error_message'
        ]