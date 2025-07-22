import os

from inference_sdk import InferenceHTTPClient
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.authtoken.models import Token


# === FOOT IMAGE PROCESSING FUNCTIONS ===
from .models import FootImage, Shoe
from .serializers import FootImageSerializer, ShoeSerializer

def process_foot_image(image_path):
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
        return None, None, f"Error processing image: {str(e)}"

def parse_predictions(result_json):
    paper_dims = None
    foot_dims = None
    try:
        predictions_data = result_json.get("predictions", {})
        predictions_list = predictions_data.get("predictions", []) if isinstance(predictions_data, dict) else predictions_data
        for pred in predictions_list:
            if isinstance(pred, dict):
                class_id = pred.get("class_id")
                width = pred.get("width")
                height = pred.get("height")
                if class_id == 2:
                    paper_dims = (width, height)
                elif class_id == 0:
                    foot_dims = (width, height)
    except Exception as e:
        pass  # Silently handle parsing errors
            
    return paper_dims, foot_dims

def score_shoe(user_length, user_width, shoe_length, shoe_width):
    length_diff = shoe_length - user_length
    width_diff = shoe_width - user_width
    if length_diff < 0 or width_diff < 0:
        return 0  # Shoe is too small
    score = 100 - (length_diff * 10 + width_diff * 10)
    return max(score, 0)

US_MENS_SIZE_TO_LENGTH = {
    7: 9.625, 7.5: 9.75, 8: 9.9375, 8.5: 10.125, 9: 10.25, 9.5: 10.4375, 10: 10.5625, 10.5: 10.75, 11: 10.9375, 11.5: 11.125, 12: 11.25
}
WIDTH_CATEGORY_TO_WIDTH = {
    'N': 3.4,  # Narrow
    'D': 3.6,  # Regular
    'W': 3.8,  # Wide
}

def get_shoe_dimensions(shoe):
    length = US_MENS_SIZE_TO_LENGTH.get(float(shoe.us_size), 10.0)
    width = WIDTH_CATEGORY_TO_WIDTH.get(shoe.width_category, 3.6)
    return length, width

# === Upload API ===

# === ENHANCED INSOLE PROCESSING FUNCTIONS ===

def calculate_hybrid_measurements(insole_points, paper_points):
    """
    Calculate measurements: bounding box L/W + real area/perimeter
    """
    import numpy as np
    
    try:
        # Convert to numpy arrays
        insole_pts = np.array([[p["x"], p["y"]] for p in insole_points])
        paper_pts = np.array([[p["x"], p["y"]] for p in paper_points])
        
        # Calculate paper reference (8.5" width)
        paper_width_pixels = np.max(paper_pts[:, 0]) - np.min(paper_pts[:, 0])
        pixels_per_inch = paper_width_pixels / 8.5
        
        # SIMPLE: Bounding box length/width
        length_pixels = np.max(insole_pts[:, 1]) - np.min(insole_pts[:, 1])
        width_pixels = np.max(insole_pts[:, 0]) - np.min(insole_pts[:, 0])
        
        # ACCURATE: Real area using Shoelace formula
        def polygon_area(points):
            x, y = points[:, 0], points[:, 1]
            return 0.5 * abs(sum(x[i]*y[i+1] - x[i+1]*y[i] for i in range(-1, len(x)-1)))
        
        # ACCURATE: Real perimeter
        def polygon_perimeter(points):
            distances = np.sqrt(np.sum((points - np.roll(points, -1, axis=0))**2, axis=1))
            return np.sum(distances)
        
        # Calculate measurements
        area_pixels = polygon_area(insole_pts)
        perimeter_pixels = polygon_perimeter(insole_pts)
        
        # Convert to inches
        return {
            'length': round(length_pixels / pixels_per_inch, 2),
            'width': round(width_pixels / pixels_per_inch, 2),
            'perimeter': round(perimeter_pixels / pixels_per_inch, 2),
            'area': round(area_pixels / (pixels_per_inch ** 2), 2)
        }
        
    except Exception as e:
        # Return None values if calculation fails
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
    Extracts polygon data from workflow format
    """
    try:
        # Extract predictions from workflow format
        predictions = result_json[0]["predictions"]["predictions"]
        
        # Find insole and paper data
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
            
        # Extract polygon points
        insole_points = insole_data.get("points", [])
        paper_points = paper_data.get("points", [])
        
        if not insole_points or not paper_points:
            return None, None, "No polygon points found"
            
        # Calculate all measurements
        measurements = calculate_hybrid_measurements(insole_points, paper_points)
        
        if measurements.get('error'):
            return None, None, f"Calculation error: {measurements['error']}"
            
        return measurements, None, None
        
    except Exception as e:
        return None, None, f"Processing error: {str(e)}"


def process_insole_image_with_enhanced_measurements(image_path):
    """
    Process an insole image using Roboflow workflow with enhanced measurements
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

        # Process the results
        measurements, error_data, error_msg = process_insole_segmentation_data(result)
        
        if error_msg:
            return None, None, None, None, error_msg
        
        return (measurements['length'], measurements['width'], 
                measurements['perimeter'], measurements['area'], None)
        
    except Exception as e:
        return None, None, None, None, f"Error processing insole image: {str(e)}"


# === API ENDPOINTS ===
@method_decorator(csrf_exempt, name='dispatch')
class FootImageUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        print("Upload endpoint hit")
        print("Request FILES:", request.FILES)
        print("Request DATA:", request.data)
        serializer = FootImageSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save(user=request.user)
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


# === SHOE API ENDPOINTS ===

@api_view(['GET'])
@permission_classes([AllowAny])
def shoe_list(request):
    """Get list of all active shoes"""
    shoes = Shoe.objects.filter(is_active=True)
    
    # Filter by parameters if provided
    company = request.GET.get('company')
    gender = request.GET.get('gender')
    function = request.GET.get('function')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    if company:
        shoes = shoes.filter(company__icontains=company)
    if gender:
        shoes = shoes.filter(gender=gender)
    if function:
        shoes = shoes.filter(function=function)
    if min_price:
        shoes = shoes.filter(price_usd__gte=min_price)
    if max_price:
        shoes = shoes.filter(price_usd__lte=max_price)
    
    serializer = ShoeSerializer(shoes, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def shoe_detail(request, pk):
    """Get details of a specific shoe"""
    try:
        shoe = Shoe.objects.get(pk=pk, is_active=True)
        serializer = ShoeSerializer(shoe, context={'request': request})
        return Response(serializer.data)
    except Shoe.DoesNotExist:
        return Response({'error': 'Shoe not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def shoe_recommendations(request):
    """Get shoe recommendations based on foot measurements"""
    length = request.GET.get('length')
    width = request.GET.get('width')
    
    if not length or not width:
        return Response({'error': 'Length and width parameters required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        length = float(length)
        width = float(width)
    except ValueError:
        return Response({'error': 'Invalid length or width values'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Find shoes with similar insole measurements (within tolerance)
    tolerance = 0.5  # inches
    
    shoes = Shoe.objects.filter(
        is_active=True,
        insole_length__isnull=False,
        insole_width__isnull=False,
        insole_length__gte=length - tolerance,
        insole_length__lte=length + tolerance,
        insole_width__gte=width - tolerance,
        insole_width__lte=width + tolerance
    ).order_by('price_usd')
    
    serializer = ShoeSerializer(shoes, many=True, context={'request': request})
    return Response({
        'foot_measurements': {
            'length': length,
            'width': width
        },
        'recommendations': serializer.data,
        'count': len(serializer.data)
    })


# === CSRF TOKEN ===

@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({"csrfToken": request.META.get("CSRF_COOKIE", "")})


# === AUTH APIs ===

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


@api_view(['GET'])
def recommendations(request):
    foot_image = FootImage.objects.filter(status='complete').order_by('-uploaded_at').first()
    if not foot_image or foot_image.length_inches is None or foot_image.width_inches is None:
        return Response({'error': 'No completed foot measurement found. Please upload and process a foot image first.'}, status=400)
    user_length = foot_image.length_inches
    user_width = foot_image.width_inches
    shoes = Shoe.objects.filter(is_active=True)
    scored_shoes = []
    for shoe in shoes:
        shoe_length, shoe_width = get_shoe_dimensions(shoe)
        score = score_shoe(user_length, user_width, shoe_length, shoe_width)
        scored_shoes.append((score, shoe))
    scored_shoes.sort(reverse=True, key=lambda x: x[0])
    result = []
    for score, shoe in scored_shoes:
        data = ShoeSerializer(shoe).data
        data['fit_score'] = score
        result.append(data)
    return Response(result)
  
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_latest_measurement(request):
    try:
        latest = FootImage.objects.filter(user=request.user, status='complete').order_by('-uploaded_at').first()
        if not latest:
            return Response({"error": "No measurements found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "id": latest.id,
            "length_inches": latest.length_inches,
            "width_inches": latest.width_inches,
            "created_at": latest.uploaded_at.isoformat(),
            "status": latest.status
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    username = request.data.get('username')
    password = request.data.get('password')

    # Verify username matches
    if username != request.user.username:
        return Response(
            {"error": "Username confirmation failed"}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify password
    if not request.user.check_password(password):
        return Response(
            {"error": "Invalid password"}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    # Delete token
    Token.objects.filter(user=request.user).delete()

    # Delete user and cascade to related FootImages
    request.user.delete()
    print("DELETE account called")
    return Response(
        {"message": "Account deleted successfully"}, 
        status=status.HTTP_200_OK
    )
