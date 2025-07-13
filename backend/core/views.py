from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.authtoken.models import Token

from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import FootImage
from .serializers import FootImageSerializer


# === Upload API ===
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


# === Detail API ===
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


# === CSRF Token ===
@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({ "csrfToken": request.META.get("CSRF_COOKIE", "") })


# === Auth APIs ===
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username and password required"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"message": "User created", "token": token.key}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    return Response({
        "username": request.user.username,
        "email": request.user.email,
        "id": request.user.id
    })


@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
