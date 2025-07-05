from rest_framework import serializers
from django.contrib.auth.models import User

from .models import FootImage, Brand, Shoe, ShoeMeasurement, FootMeasurement, Recommendation

'''
class FootImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FootImage
        fields = ['id', 'image', 'uploaded_at']

'''
# Added Serializations to New attributes ----- SECURITY WARNING

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class FootImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FootImage
        fields = ['id', 'image', 'uploaded_at', 'processed']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'description']

class ShoeMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoeMeasurement
        fields = ['id', 'size_us', 'size_eu', 'length_mm', 'width_mm', 'arch_height_mm']

class ShoeSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    measurements = ShoeMeasurementSerializer(many=True, read_only=True)
    
    class Meta:
        model = Shoe
        fields = ['id', 'brand', 'model_name', 'style_code', 'price_range', 'measurements']

class FootMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = FootMeasurement
        fields = ['id', 'foot_length_mm', 'foot_width_mm', 'arch_height_mm', 'measurement_confidence', 'measurement_date']

class RecommendationSerializer(serializers.ModelSerializer):
    shoe = ShoeSerializer(read_only=True)
    
    class Meta:
        model = Recommendation
        fields = ['id', 'shoe', 'recommended_size_us', 'similarity_score', 'confidence_score', 'recommendation_date']
