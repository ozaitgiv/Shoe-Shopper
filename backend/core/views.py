import os
from inference_sdk import InferenceHTTPClient
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
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

def process_foot_image(image_path):
    """Process the foot image using Roboflow CV model"""
    try:
        client = InferenceHTTPClient(
            api_url="https://serverless.roboflow.com",
            api_key=os.environ.get("ROBOFLOW_API_KEY")
        )

        result = client.run_workflow(
            workspace_name="armaanai",
            workflow_id="foot-measuring",
            images={"image": image_path},
            use_cache=True
        )

        result_json = result[0]
        paper_dims, foot_dims = parse_predictions(result_json)
        
        if paper_dims is None:
            return None, None, "Paper not detected in the image"
        if foot_dims is None:
            return None, None, "Foot not detected in the image"
        
        pixels_per_inch = paper_dims[0] / 8.5
        length_inches = round(foot_dims[1] / pixels_per_inch, 2)
        width_inches = round(foot_dims[0] / pixels_per_inch, 2)
        
        return length_inches, width_inches, None
        
    except Exception as e:
        error_msg = f"Error processing image: {str(e)}"
        return None, None, error_msg


def parse_predictions(result_json):
    """Parse CV model predictions"""
    paper_dims = None
    foot_dims = None
    
    try:
        predictions_data = result_json.get("predictions", {})
        if isinstance(predictions_data, dict):
            predictions_list = predictions_data.get("predictions", [])
        else:
            predictions_list = predictions_data
        
        for pred in predictions_list:
            if isinstance(pred, dict):
                class_id = pred.get("class_id")
                width = pred.get("width")
                height = pred.get("height")
                
                if class_id == 2:  # Paper
                    paper_dims = (width, height)
                elif class_id == 0:  # Foot
                    foot_dims = (width, height)
    except Exception as e:
        print(f"Error parsing predictions: {e}")
            
    return paper_dims, foot_dims

# === Upload API ===
@method_decorator(csrf_exempt, name='dispatch')
class FootImageUploadView(APIView):
    def post(self, request, format=None):
        print(" Upload endpoint hit")
        print("Request FILES:", request.FILES)
        print("Request DATA:", request.data)

        serializer = FootImageSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()

            # Process with CV model
            try:
                image_path = instance.image.path
                length, width, error_msg = process_foot_image(image_path)
            
                if error_msg:
                    instance.status = 'error'
                    instance.error_message = error_msg
                else:
                    instance.status = 'complete'
                    instance.length_inches = length
                    instance.width_inches = width
            
                instance.save()
            
            except Exception as e:
                instance.status = 'error'
                instance.error_message = f"Unexpected error: {str(e)}"
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
            response_data["error_message"] = foot_image.error_message or "There was an error processing your image."

        return Response(response_data)


# === CSRF Token ===
@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({ "csrfToken": request.META.get("CSRF_COOKIE", "") })


# === Auth APIs ===
@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
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
