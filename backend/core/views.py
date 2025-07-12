from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import FootImage
from .serializers import FootImageSerializer

class FootImageUploadView(APIView):
    def post(self, request, format=None):
        print(" Upload endpoint hit")
        print("Request FILES:", request.FILES)
        print("Request DATA:", request.data)

        serializer = FootImageSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()

            # Simulate processing
            instance.status = 'complete'
            instance.length_inches = 10.2
            instance.width_inches = 4.1
            instance.save()

            return Response({ "measurement_id": instance.id }, status=status.HTTP_201_CREATED)
        
        print(" Serializer errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FootImageDetailView(APIView):
    def get(self, request, pk, format=None):
        foot_image = get_object_or_404(FootImage, pk=pk)

        response_data = {
            "id": foot_image.id,
            "status": foot_image.status,
            "created_at": foot_image.uploaded_at.isoformat(),
            "image_url": foot_image.image.url if foot_image.image else None,
        }

        if foot_image.status == "complete":
            response_data["length_inches"] = foot_image.length_inches
            response_data["width_inches"] = foot_image.width_inches

        if foot_image.status == "error":
            response_data["error_message"] = "There was an error processing your image."

        return Response(response_data)



from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse

@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({ "csrfToken": request.META.get("CSRF_COOKIE", "") })
