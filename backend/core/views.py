'''
from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import FootImageSerializer

def upload_form_view(request):
    return render(request, 'upload_form.html')

class FootImageUploadView(APIView):
    def post(self, request, format=None):
        serializer = FootImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

'''

# UPDATED - - - IN-DEPTH SCRIPT FOR IMAGE UPLOAD AND MEASUREMENT PROCESSING

import os
import subprocess
import json
from django.conf import settings
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FootImage, FootMeasurement
from .serializers import FootImageSerializer, FootMeasurementSerializer

def upload_form_view(request):
    return render(request, 'upload_form.html')

class FootImageUploadView(APIView):
    def post(self, request):
        serializer = FootImageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Save image
        foot_image = serializer.save(user=request.user)

        try:
            # Run measurement script
            image_path = os.path.join(settings.MEDIA_ROOT, str(foot_image.image))
            result = subprocess.run(
                ["python", "cv/run_insole_measurement.py", image_path],
                capture_output=True,
                text=True,
                check=True
            )

            data = json.loads(result.stdout)
            paper_dims = data['paper_in_inches']
            insole_dims = data['insole_in_inches']

            # Convert inches to mm
            foot_length_mm = round(insole_dims[0] * 25.4, 2)
            foot_width_mm = round(insole_dims[1] * 25.4, 2)

            # Save foot measurement
            FootMeasurement.objects.create(
                user=request.user,
                foot_length_mm=foot_length_mm,
                foot_width_mm=foot_width_mm
            )

            foot_image.processed = True
            foot_image.save()

            return Response({
                "message": "Image processed successfully",
                "measurements": {
                    "length_mm": foot_length_mm,
                    "width_mm": foot_width_mm
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            foot_image.error_message = str(e)
            foot_image.save()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


