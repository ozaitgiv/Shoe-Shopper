import os
import numpy as np
from inference_sdk import InferenceHTTPClient
from dotenv import load_dotenv
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

from pathlib import Path
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)

# ===== AUTH FUNCTIONS =====
@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'csrfToken': request.META.get('CSRF_COOKIE')})

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        first_name=first_name,
        last_name=last_name
    )
    
    token, created = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user_id': user.id,
        'username': user.username
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        request.user.auth_token.delete()
        logout(request)
        return Response({'message': 'Successfully logged out'})
    except:
        return Response({'error': 'Logout failed'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    })

# ===== IMAGE PROCESSING FUNCTIONS =====

def process_foot_image(image_path):
    """Process the foot image using Roboflow CV model (ORIGINAL FUNCTION)"""
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

# ===== ENHANCED MEASUREMENT FUNCTIONS =====

def calculate_hybrid_measurements(insole_points, paper_points):
    """
    Calculate measurements: bounding box L/W + real area/perimeter
    """
    try:
        insole_pts = np.array([[p["x"], p["y"]] for p in insole_points])
        paper_pts = np.array([[p["x"], p["y"]] for p in paper_points])
        
        paper_width_pixels = np.max(paper_pts[:, 0]) - np.min(paper_pts[:, 0])
        pixels_per_inch = paper_width_pixels / 8.5
        
        length_pixels = np.max(insole_pts[:, 1]) - np.min(insole_pts[:, 1])
        width_pixels = np.max(insole_pts[:, 0]) - np.min(insole_pts[:, 0])
        
        def polygon_area(points):
            x, y = points[:, 0], points[:, 1]
            return 0.5 * abs(sum(x[i]*y[i+1] - x[i+1]*y[i] for i in range(-1, len(x)-1)))
        
        def polygon_perimeter(points):
            distances = np.sqrt(np.sum((points - np.roll(points, -1, axis=0))**2, axis=1))
            return np.sum(distances)
        
        area_pixels = polygon_area(insole_pts)
        perimeter_pixels = polygon_perimeter(insole_pts)
        
        return {
            'length': round(length_pixels / pixels_per_inch, 2),
            'width': round(width_pixels / pixels_per_inch, 2),
            'perimeter': round(perimeter_pixels / pixels_per_inch, 2),
            'area': round(area_pixels / (pixels_per_inch ** 2), 2)
        }
        
    except Exception as e:
        return {
            'length': None,
            'width': None, 
            'perimeter': None,
            'area': None,
            'error': str(e)
        }

def process_insole_segmentation_data(result_json):
    """
    Process segmentation workflow results
    """
    try:
        predictions = result_json[0]["predictions"]["predictions"]
        
        insole_data = None
        paper_data = None
        
        for pred in predictions:
            if pred.get("class") == "Insole":
                insole_data = pred
            elif pred.get("class") == "Paper":
                paper_data = pred
        
        if insole_data is None:
            return None, None, "Insole not detected in image"
        if paper_data is None:
            return None, None, "Paper not detected in image"
            
        insole_points = insole_data.get("points", [])
        paper_points = paper_data.get("points", [])
        
        if not insole_points or not paper_points:
            return None, None, "No polygon points found"
            
        measurements = calculate_hybrid_measurements(insole_points, paper_points)
        
        if measurements.get('error'):
            return None, None, f"Calculation error: {measurements['error']}"
            
        return measurements, None, None
        
    except Exception as e:
        return None, None, f"Processing error: {str(e)}"

def process_insole_image_with_enhanced_measurements(image_path):
    """
    Process an insole image using existing workflow & enhanced measurements
    """
    try:
        client = InferenceHTTPClient(
            api_url="https://serverless.roboflow.com",
            api_key=os.environ.get("ROBOFLOW_API_KEY")
        )

        result = client.run_workflow(
            workspace_name="armaanai",
            workflow_id="insole-measuring",
            images={"image": image_path},
            use_cache=True
        )

        measurements, error_data, error_msg = process_insole_segmentation_data(result)
        
        if error_msg:
            return None, None, None, None, error_msg
        
        return (measurements['length'], measurements['width'], 
                measurements['perimeter'], measurements['area'], None)
        
    except Exception as e:
        return None, None, None, None, f"Error processing insole image: {str(e)}"

# ===== API VIEWS =====

@method_decorator(csrf_exempt, name='dispatch')
class FootImageUploadView(APIView):
    def post(self, request, format=None):
        print("Upload endpoint hit")
        print("Request FILES:", request.FILES)
        print("Request DATA:", request.data)
        print("User authenticated: {request.user.is_authenticated}")
        if request.user.is_authenticated:
            print("Current user: {request.user.username} (ID: {request.user.id})")

        serializer = FootImageSerializer(data=request.data)
        if serializer.is_valid():
            
            if request.user.is_authenticated:
                user = request.user
                print(f"Using authenticated user: {user.username}")
            else:
                user, created = User.objects.get_or_create(
                    username='anonymous_user',
                    defaults={
                        'email': 'anonymous@example.com',
                        'first_name': 'Anonymous',
                        'last_name': 'User'
                    }
                )
                print(f"Using test user: {user.username} (created: {created})")
            
            instance = serializer.save(user=user)
            print(f"FootImage created: ID={instance.id}, User={instance.user.username}")

            try:
                image_path = instance.image.path
                print(f"Processing image: {image_path}")
                
                try:
                    length, width, perimeter, area, error_msg = process_insole_image_with_enhanced_measurements(image_path)
                    
                    if error_msg:
                        print(f"Enhanced processing failed: {error_msg}")
                        print(f"Falling back to basic processing...")
                        length, width, basic_error = process_foot_image(image_path)
                        error_msg = basic_error
                        perimeter = None
                        area = None
                    else:
                        print(f"Enhanced processing successful!")
                        print(f"All measurements captured: L={length}\", W={width}\", P={perimeter}\", A={area} sq in")
                        
                except Exception as e:
                    print(f"⚠️ Enhanced processing exception: {str(e)}")
                    length, width, error_msg = process_foot_image(image_path)
                    perimeter = None
                    area = None
            
                if error_msg:
                    instance.status = 'error'
                    instance.error_message = error_msg
                    print(f"Processing failed: {error_msg}")
                else:
                    instance.status = 'complete'
                    
                    instance.length_inches = length
                    instance.width_inches = width
                    instance.perimeter_inches = perimeter  
                    instance.area_sq_inches = area         
                    
                    print(f"Storing measurements in database:")
                    print(f"Length: {instance.length_inches}")
                    print(f"Width: {instance.width_inches}")
                    print(f"Perimeter: {instance.perimeter_inches}")
                    print(f"Area: {instance.area_sq_inches}")
            
                instance.save()
                print(f"Instance saved with status: {instance.status}")
                
                instance.refresh_from_db()
                print(f"Verification - Database contains:")
                print(f"Length: {instance.length_inches}")
                print(f"Width: {instance.width_inches}")
                print(f"Perimeter: {instance.perimeter_inches}")
                print(f"Area: {instance.area_sq_inches}")
            
            except Exception as e:
                print(f"Processing exception: {str(e)}")
                import traceback
                traceback.print_exc()
                instance.status = 'error'
                instance.error_message = f"Unexpected error: {str(e)}"
                instance.save()

            return Response({ "measurement_id": instance.id }, status=status.HTTP_201_CREATED)
        
        print("Serializer errors:", serializer.errors)
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
            response_data["error_message"] = foot_image.error_message or "There was an error processing your image."

        return Response(response_data)