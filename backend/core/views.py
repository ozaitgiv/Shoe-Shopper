import os
import logging

from inference_sdk import InferenceHTTPClient

logger = logging.getLogger(__name__)

# Constants for shoe fitting algorithm
FIT_THRESHOLDS = {
    'EXCELLENT': 90,
    'GOOD': 75, 
    'FAIR': 60,
    'POOR': 0
}

# Scoring tolerance constants
PERIMETER_PERFECT_MIN = 0.95
PERIMETER_PERFECT_MAX = 1.05
PERIMETER_MAX_RATIO = 1.15
AREA_PERFECT_MIN = 0.9
AREA_PERFECT_MAX = 1.0
AREA_MAX_RATIO = 1.1
LENGTH_MAX_RATIO = 1.15
WIDTH_TOLERANCE_PCT = 0.1

# Foot shape estimation constants
FOOT_AREA_SHAPE_FACTOR = 0.7  # Research-based foot area factor
SHOE_AREA_SHAPE_FACTOR = 0.75  # Slightly larger than foot

# Critical scoring threshold for safety
CRITICAL_LENGTH_THRESHOLD = 40

def cleanup_old_guest_sessions():
    """Clean up guest sessions older than 7 days to prevent database bloat"""
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    cutoff_date = timezone.now() - timedelta(days=7)
    
    try:
        # Delete old guest foot images
        old_guest_images = FootImage.objects.filter(
            user__isnull=True,
            error_message__startswith='GUEST_SESSION:',
            uploaded_at__lt=cutoff_date
        )
        
        count = old_guest_images.count()
        old_guest_images.delete()
        
        logger.info(f"Cleaned up {count} old guest sessions")
        return count
    except Exception as e:
        logger.error(f"Error cleaning up guest sessions: {str(e)}")
        return 0

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

def process_foot_image_enhanced(image_path, paper_size="letter"):
    """
    Enhanced foot processing using segmentation workflow for 4D measurements
    """
    try:
        client = InferenceHTTPClient(
            api_url="https://serverless.roboflow.com",
            api_key=os.environ.get("ROBOFLOW_API_KEY")
        )
        
        # Use the working foot-measuring workflow (foot-segmentation doesn't exist yet)
        result = client.run_workflow(
            workspace_name="armaanai",
            workflow_id="foot-measuring",
            images={"image": image_path},
            use_cache=True
        )
        result_json = result[0]
        paper_dims, foot_dims = parse_predictions(result_json)
        
        if paper_dims is None:
            return None, None, None, None, "Paper not detected in the image"
        if foot_dims is None:
            return None, None, None, None, "Foot not detected in the image"
        
        # Use correct paper width based on paper size
        paper_width_inches = 8.5 if paper_size == "letter" else 8.27
        pixels_per_inch = paper_dims[0] / paper_width_inches
        
        length_inches = round(foot_dims[1] / pixels_per_inch, 2)
        width_inches = round(foot_dims[0] / pixels_per_inch, 2)
        
        # Estimate area and perimeter from bounding box
        area_sqin = estimate_foot_area_from_dimensions(length_inches, width_inches)
        perimeter_inches = estimate_foot_perimeter_from_dimensions(length_inches, width_inches)
        
        return length_inches, width_inches, area_sqin, perimeter_inches, None
        
    except Exception as e:
        return None, None, None, None, f"Error processing image: {str(e)}"

def process_foot_image(image_path, paper_size="letter"):
    """
    Legacy function - delegates to enhanced version and returns only length/width for compatibility
    """
    length, width, area, perimeter, error = process_foot_image_enhanced(image_path, paper_size)
    return length, width, error

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
    except (KeyError, AttributeError, TypeError) as e:
        logger.debug("Error parsing predictions", extra={'error': str(e)})
            
    return paper_dims, foot_dims

def process_foot_segmentation_data(result_json, paper_size="letter"):
    """
    Process foot segmentation workflow results (similar to insole processing)
    """
    try:
        # Extract predictions from workflow format
        predictions = result_json[0]["predictions"]["predictions"]
        
        # Find foot and paper data
        foot_data = None
        paper_data = None
        
        for pred in predictions:
            if pred.get("class") == "Foot":
                foot_data = pred
            elif pred.get("class") == "Paper":
                paper_data = pred
        
        if foot_data is None:
            return None, None, "Foot not detected in image"
        if paper_data is None:
            return None, None, "Paper not detected in image"
            
        # Extract polygon points
        foot_points = foot_data.get("points", [])
        paper_points = paper_data.get("points", [])
        
        if not foot_points or not paper_points:
            return None, None, "No polygon points found"
            
        # Calculate all measurements with paper size
        measurements = calculate_hybrid_measurements(foot_points, paper_points, paper_size)
        
        if measurements.get('error'):
            return None, None, f"Calculation error: {measurements['error']}"
            
        return measurements, None, None
        
    except Exception as e:
        return None, None, f"Processing error: {str(e)}"

def estimate_foot_area_from_dimensions(length_inches, width_inches):
    """
    Estimate foot area from bounding box dimensions using foot shape factor
    Research shows foot area ≈ 0.7 * bounding box area for typical foot shapes
    """
    if length_inches and width_inches:
        return round(length_inches * width_inches * FOOT_AREA_SHAPE_FACTOR, 2)
    return None

def estimate_foot_perimeter_from_dimensions(length_inches, width_inches):
    """
    Estimate foot perimeter from bounding box using ellipse approximation
    """
    if length_inches and width_inches:
        # Use Ramanujan's approximation for ellipse perimeter
        a, b = length_inches / 2, width_inches / 2
        h = ((a - b) / (a + b)) ** 2
        perimeter = 3.14159 * (a + b) * (1 + (3 * h) / (10 + (4 - 3 * h) ** 0.5))
        return round(2 * perimeter, 2)  # Double because we used semi-axes
    return None

# === ENHANCED RECOMMENDATION ALGORITHM ===

def get_real_shoe_dimensions_4d(shoe):
    """
    Get all 4 shoe dimensions: length, width, area, perimeter
    Use real measurements if available, fallback to estimations
    """
    try:
        if shoe.insole_length and shoe.insole_width:
            # Use actual measured dimensions
            length = shoe.insole_length
            width = shoe.insole_width
            area = shoe.insole_area if shoe.insole_area else estimate_shoe_area_from_dimensions(length, width)
            perimeter = shoe.insole_perimeter if shoe.insole_perimeter else estimate_shoe_perimeter_from_dimensions(length, width)
            
            logger.debug("Using measured shoe dimensions", extra={
                'shoe_id': shoe.id, 'length': length, 'width': width, 
                'has_area': bool(shoe.insole_area), 'has_perimeter': bool(shoe.insole_perimeter)
            })
            return length, width, area, perimeter
        else:
            # Fallback to static mapping for shoes without measurements
            US_MENS_SIZE_TO_LENGTH = {
                7: 9.625, 7.5: 9.75, 8: 9.9375, 8.5: 10.125, 9: 10.25, 
                9.5: 10.4375, 10: 10.5625, 10.5: 10.75, 11: 10.9375, 
                11.5: 11.125, 12: 11.25, 12.5: 11.4375, 13: 11.625
            }
            WIDTH_CATEGORY_TO_WIDTH = {
                'N': 3.4,  # Narrow
                'D': 3.6,  # Regular
                'W': 3.8,  # Wide
            }
            length = US_MENS_SIZE_TO_LENGTH.get(float(shoe.us_size), 10.0)
            width = WIDTH_CATEGORY_TO_WIDTH.get(shoe.width_category, 3.6)
            area = estimate_shoe_area_from_dimensions(length, width)
            perimeter = estimate_shoe_perimeter_from_dimensions(length, width)
            
            logger.info("Using estimated shoe dimensions", extra={
                'shoe_id': shoe.id, 'us_size': shoe.us_size, 'width_category': shoe.width_category,
                'estimated_length': length, 'estimated_width': width
            })
            return length, width, area, perimeter
    except (ValueError, AttributeError) as e:
        logger.error("Error calculating shoe dimensions", extra={
            'shoe_id': getattr(shoe, 'id', None), 'error': str(e)
        })
        # Return safe defaults
        return 10.0, 3.6, 27.0, 28.0

def get_real_shoe_dimensions(shoe):
    """
    Legacy function - returns only length and width for backward compatibility
    """
    length, width, _, _ = get_real_shoe_dimensions_4d(shoe)
    return length, width

def enhanced_score_shoe_4d(user_length, user_width, user_area, user_perimeter,
                          shoe_length, shoe_width, shoe_area, shoe_perimeter, shoe_type="general"):
    """
    Enhanced 4D scoring using length, width, area, and perimeter measurements
    Based on research: length 35-40%, width 25-30%, perimeter 20-25%, area 10-15%
    """
    # Input validation - prevent division by zero and invalid data
    if any(val is None or val <= 0 for val in [user_length, user_width, shoe_length, shoe_width]):
        logger.warning("Invalid input data for scoring algorithm", extra={
            'user_length': user_length, 'user_width': user_width,
            'shoe_length': shoe_length, 'shoe_width': shoe_width
        })
        return 0  # Invalid input data
    
    # Base weights from research
    weights = {
        'length': 0.375,
        'width': 0.275,
        'perimeter': 0.225,
        'area': 0.125
    }
    
    # Shoe-type specific adjustments and clearances
    clearances = get_clearances_by_shoe_type(shoe_type)
    
    # Calculate adjusted foot measurements with clearances
    adjusted_foot = {
        'length': user_length + clearances['length'],
        'width': user_width + clearances['width'],
        'perimeter': user_perimeter + clearances['perimeter'] if user_perimeter else None,
        'area': user_area * (1 + clearances['area']) if user_area else None
    }
    
    scores = {}
    
    # Length scoring (more gradual penalties)
    length_ratio = adjusted_foot['length'] / shoe_length
    if length_ratio <= 1.0:
        scores['length'] = 100 * (0.7 + 0.3 * length_ratio)  # 70-100 range
    elif length_ratio <= 1.05:
        # Gentle penalty for slightly oversized feet (100-70 range)
        scores['length'] = 100 - (length_ratio - 1.0) * 600
    else:
        # Steeper penalty beyond 5% overage, starting from 70
        penalty_range = LENGTH_MAX_RATIO - 1.05  # 0.1
        remaining_ratio = length_ratio - 1.05
        scores['length'] = max(0, 70 - (remaining_ratio / penalty_range) * 70)
    
    # Width scoring (symmetric tolerance)
    width_diff = abs(adjusted_foot['width'] - shoe_width)
    width_tolerance = shoe_width * WIDTH_TOLERANCE_PCT
    scores['width'] = max(0, 100 * (1 - width_diff / width_tolerance))
    
    # Perimeter scoring (accounts for foot circumference)
    if adjusted_foot['perimeter'] and shoe_perimeter:
        perim_ratio = adjusted_foot['perimeter'] / shoe_perimeter
        if PERIMETER_PERFECT_MIN <= perim_ratio <= PERIMETER_PERFECT_MAX:  # Sweet spot
            scores['perimeter'] = 100
        elif perim_ratio < PERIMETER_PERFECT_MIN:
            scores['perimeter'] = max(0, 100 * (perim_ratio / PERIMETER_PERFECT_MIN))
        else:
            scores['perimeter'] = max(0, 100 * (PERIMETER_MAX_RATIO - perim_ratio) / 0.1)
    else:
        # Fallback to estimated perimeter score
        scores['perimeter'] = estimate_perimeter_score(user_length, user_width, shoe_length, shoe_width)
    
    # Area scoring (volume accommodation)
    if adjusted_foot['area'] and shoe_area:
        area_ratio = adjusted_foot['area'] / shoe_area
        if AREA_PERFECT_MIN <= area_ratio <= AREA_PERFECT_MAX:  # Foot should fit within shoe area
            scores['area'] = 100
        elif area_ratio < AREA_PERFECT_MIN:
            scores['area'] = 100 * (area_ratio / AREA_PERFECT_MIN)
        else:
            scores['area'] = max(0, 100 * (AREA_MAX_RATIO - area_ratio) / 0.1)
    else:
        # Fallback to estimated area score
        scores['area'] = estimate_area_score(user_length, user_width, shoe_length, shoe_width)
    
    # Weighted final score
    final_score = sum(weights[dim] * scores[dim] for dim in weights)
    
    # Gradual length penalty instead of harsh 50% cutoff
    if scores['length'] < CRITICAL_LENGTH_THRESHOLD:
        penalty_factor = 0.7 + 0.3 * (scores['length'] / CRITICAL_LENGTH_THRESHOLD)
        final_score *= penalty_factor
    
    return min(100, max(0, round(final_score, 1)))

def enhanced_score_shoe(user_length, user_width, shoe_length, shoe_width):
    """
    Legacy scoring function - maintained for backward compatibility
    """
    # Input validation
    if any(val is None or val <= 0 for val in [user_length, user_width, shoe_length, shoe_width]):
        return 0  # Invalid input data
    
    # Use 4D scoring with estimated area/perimeter
    user_area = estimate_foot_area_from_dimensions(user_length, user_width)
    user_perimeter = estimate_foot_perimeter_from_dimensions(user_length, user_width)
    shoe_area = estimate_shoe_area_from_dimensions(shoe_length, shoe_width)
    shoe_perimeter = estimate_shoe_perimeter_from_dimensions(shoe_length, shoe_width)
    
    return enhanced_score_shoe_4d(user_length, user_width, user_area, user_perimeter,
                                 shoe_length, shoe_width, shoe_area, shoe_perimeter)

def get_clearances_by_shoe_type(shoe_type):
    """Dynamic clearances based on shoe type (in inches)"""
    clearance_configs = {
        'running': {
            'length': 0.5,    # ~12.5mm
            'width': 0.08,    # ~2mm 
            'perimeter': 0.4, # Accommodate foot expansion
            'area': 0.15      # 15% area increase
        },
        'hiking': {
            'length': 0.6,    # ~15mm
            'width': 0.12,    # ~3mm
            'perimeter': 0.6,
            'area': 0.2
        },
        'casual': {
            'length': 0.25,   # ~6mm
            'width': 0.04,    # ~1mm
            'perimeter': 0.2,
            'area': 0.1
        },
        'work': {
            'length': 0.4,    # ~10mm
            'width': 0.08,    # ~2mm
            'perimeter': 0.3,
            'area': 0.12
        }
    }
    return clearance_configs.get(shoe_type, clearance_configs['casual'])

def estimate_perimeter_score(user_length, user_width, shoe_length, shoe_width):
    """Estimate perimeter fit score from length/width"""
    user_perim = estimate_foot_perimeter_from_dimensions(user_length, user_width)
    shoe_perim = estimate_shoe_perimeter_from_dimensions(shoe_length, shoe_width)
    if user_perim and shoe_perim:
        ratio = user_perim / shoe_perim
        if 0.95 <= ratio <= 1.05:
            return 100
        elif ratio < 0.95:
            return max(0, 100 * (ratio / 0.95))
        else:
            return max(0, 100 * (1.15 - ratio) / 0.1)
    return 75  # Default moderate score

def estimate_area_score(user_length, user_width, shoe_length, shoe_width):
    """Estimate area fit score from length/width"""
    user_area = estimate_foot_area_from_dimensions(user_length, user_width)
    shoe_area = estimate_shoe_area_from_dimensions(shoe_length, shoe_width)
    if user_area and shoe_area:
        ratio = user_area / shoe_area
        if 0.9 <= ratio <= 1.0:
            return 100
        elif ratio < 0.9:
            return 100 * (ratio / 0.9)
        else:
            return max(0, 100 * (1.1 - ratio) / 0.1)
    return 75  # Default moderate score

def estimate_shoe_area_from_dimensions(length_inches, width_inches):
    """Estimate shoe insole area from dimensions"""
    if length_inches and width_inches:
        return round(length_inches * width_inches * SHOE_AREA_SHAPE_FACTOR, 2)  # Slightly higher than foot
    return None

def estimate_shoe_perimeter_from_dimensions(length_inches, width_inches):
    """Estimate shoe insole perimeter from dimensions"""
    if length_inches and width_inches:
        # Similar to foot but slightly larger
        a, b = length_inches / 2, width_inches / 2
        h = ((a - b) / (a + b)) ** 2
        perimeter = 3.14159 * (a + b) * (1 + (3 * h) / (10 + (4 - 3 * h) ** 0.5))
        return round(2.1 * perimeter, 2)  # Slightly larger than foot
    return None

# === ENHANCED INSOLE PROCESSING FUNCTIONS ===

def calculate_hybrid_measurements(insole_points, paper_points, paper_size="letter"):
    """
    Calculate measurements: bounding box L/W + real area/perimeter
    """
    import numpy as np
    
    try:
        # Convert to numpy arrays
        insole_pts = np.array([[p["x"], p["y"]] for p in insole_points])
        paper_pts = np.array([[p["x"], p["y"]] for p in paper_points])
        
        # Calculate paper reference based on paper size
        paper_width_inches = 8.5 if paper_size == "letter" else 8.27  # A4 width is 8.27"
        paper_width_pixels = np.max(paper_pts[:, 0]) - np.min(paper_pts[:, 0])
        pixels_per_inch = paper_width_pixels / paper_width_inches
        
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


def process_insole_segmentation_data(result_json, paper_size="letter"):
    """
    Process segmentation workflow results
    Extracts polygon data from workflow format
    """
    try:
        # Extract predictions from workflow format
        predictions = result_json[0]["predictions"]["predictions"]
        
        logger.debug(f"Processing {len(predictions)} predictions")
        
        # Find insole and paper data
        insole_data = None
        paper_data = None
        
        for pred in predictions:
            class_name = pred.get("class")
            logger.debug(f"Found prediction with class: {class_name}")
            
            if pred.get("class") == "Insole":
                insole_data = pred
                logger.debug("Found Insole data")
            elif pred.get("class") == "Paper":
                paper_data = pred
                logger.debug("Found Paper data")
        
        if insole_data is None:
            return None, None, "Insole not detected in image"
        if paper_data is None:
            return None, None, "Paper not detected in image"
            
        # Extract polygon points
        insole_points = insole_data.get("points", [])
        paper_points = paper_data.get("points", [])
        
        if not insole_points or not paper_points:
            return None, None, "No polygon points found"
            
        # Calculate all measurements with paper size
        measurements = calculate_hybrid_measurements(insole_points, paper_points, paper_size)
        
        if measurements.get('error'):
            return None, None, f"Calculation error: {measurements['error']}"
            
        return measurements, None, None
        
    except Exception as e:
        return None, None, f"Processing error: {str(e)}"


def process_insole_image_with_enhanced_measurements(image_path, paper_size="letter"):
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

        # Process the results with paper size
        measurements, error_data, error_msg = process_insole_segmentation_data(result, paper_size)
        
        if error_msg:
            return None, None, None, None, error_msg
        
        return (measurements['length'], measurements['width'], 
                measurements['perimeter'], measurements['area'], None)
        
    except Exception as e:
        return None, None, None, None, f"Error processing insole image: {str(e)}"


# === API ENDPOINTS ===
@method_decorator(csrf_exempt, name='dispatch')
class FootImageUploadView(APIView):
    permission_classes = [AllowAny]  # Allow guests without authentication

    def post(self, request, format=None):
        logger.info("Foot image upload endpoint accessed", extra={
            'user_authenticated': request.user.is_authenticated,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'has_files': bool(request.FILES),
        })
        
        try:
            # Handle both authenticated users and guests
            user = request.user if request.user.is_authenticated else None
            
            # For guests, ensure we have a session
            guest_session_key = None
            if not user:
                if not request.session.session_key:
                    request.session.create()
                guest_session_key = request.session.session_key
                logger.info("Guest session created/retrieved", extra={
                    'session_key': guest_session_key[:8] + '...'  # Log partial key for debugging
                })
            
            serializer = FootImageSerializer(data=request.data)
            if serializer.is_valid():
                logger.info("FootImage serializer validation successful")
                instance = serializer.save(user=user)
                
                # For guests, store session key in error_message field temporarily
                # This is a safe approach that doesn't require database schema changes
                if guest_session_key:
                    instance.error_message = f"GUEST_SESSION:{guest_session_key}"
                    instance.save()
                    
                    # Occasionally cleanup old guest sessions (10% chance)
                    import random
                    if random.random() < 0.1:  # 10% chance
                        cleanup_old_guest_sessions()
                
                logger.info("FootImage instance created", extra={
                    'instance_id': instance.id,
                    'is_guest': user is None,
                    'has_session': guest_session_key is not None
                })
                
                try:
                    image_path = instance.image.path
                    
                    # Get paper size from request, default to 'letter'
                    paper_size = request.data.get('paper_size', 'letter')
                    logger.debug("Processing foot image", extra={
                        'image_path': image_path,
                        'paper_size': paper_size
                    })
                    
                    length, width, area, perimeter, error_msg = process_foot_image_enhanced(image_path, paper_size)
                    if error_msg:
                        logger.error("Foot image processing failed", extra={
                            'instance_id': instance.id,
                            'error_message': error_msg
                        })
                        instance.status = 'error'
                        instance.error_message = error_msg
                    else:
                        logger.info("Foot image processing completed successfully", extra={
                            'instance_id': instance.id,
                            'length': length,
                            'width': width,
                            'area': area,
                            'perimeter': perimeter
                        })
                        instance.status = 'complete'
                        instance.length_inches = length
                        instance.width_inches = width
                        instance.area_sqin = area
                        instance.perimeter_inches = perimeter
                    instance.save()
                except Exception as e:
                    logger.exception("Unexpected error during foot image processing", extra={
                        'instance_id': instance.id,
                        'error': str(e)
                    })
                    instance.status = 'error'
                    instance.error_message = f"Unexpected error: {str(e)}"
                    instance.save()

                return Response({ "measurement_id": instance.id }, status=status.HTTP_201_CREATED)
            else:
                logger.warning("FootImage serializer validation failed", extra={
                    'errors': serializer.errors
                })
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.exception("Unexpected error in upload view", extra={
                'error': str(e)
            })
            return Response({
                "error": f"Server error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FootImageDetailView(APIView):
    permission_classes = [AllowAny]  # Allow guests to check their measurement status
    
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
            response_data["area_sqin"] = foot_image.area_sqin
            response_data["perimeter_inches"] = foot_image.perimeter_inches
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


@api_view(['GET'])  
@permission_classes([AllowAny])
def shoe_list_with_scores(request):
    """Get all shoes with fit scores for authenticated users"""
    shoes = Shoe.objects.filter(is_active=True)
    
    # If user is authenticated and has measurements, add fit scores
    if request.user.is_authenticated:
        foot_image = FootImage.objects.filter(
            user=request.user,
            status='complete'
        ).order_by('-uploaded_at').first()
        
        if foot_image and foot_image.length_inches and foot_image.width_inches:
            user_length = foot_image.length_inches
            user_width = foot_image.width_inches
            
            result = []
            for shoe in shoes:
                shoe_length, shoe_width, shoe_area, shoe_perimeter = get_real_shoe_dimensions_4d(shoe)
                
                # Use 4D scoring if foot measurements available, otherwise fallback
                if foot_image.area_sqin and foot_image.perimeter_inches:
                    score = enhanced_score_shoe_4d(
                        user_length, user_width, foot_image.area_sqin, foot_image.perimeter_inches,
                        shoe_length, shoe_width, shoe_area, shoe_perimeter, shoe.function
                    )
                else:
                    # Fallback to legacy scoring for older measurements
                    score = enhanced_score_shoe(user_length, user_width, shoe_length, shoe_width)
                
                data = ShoeSerializer(shoe, context={'request': request}).data
                data['fit_score'] = score
                result.append(data)
            
            # Sort by fit score
            result.sort(key=lambda x: x.get('fit_score', 0), reverse=True)
            return Response(result)
    
    # For unauthenticated users or users without measurements
    serializer = ShoeSerializer(shoes, many=True, context={'request': request})
    return Response(serializer.data)


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
@permission_classes([AllowAny])
def recommendations(request):
    """Get shoe recommendations using real insole measurements"""
    # Support both authenticated users and guests
    if request.user.is_authenticated:
        foot_image = FootImage.objects.filter(
            user=request.user, 
            status='complete'
        ).order_by('-uploaded_at').first()
    else:
        # For guests, filter by session key to isolate their data
        session_key = request.session.session_key
        if not session_key:
            # No session means no previous uploads
            foot_image = None
        else:
            # Find guest images that belong to this session
            foot_image = FootImage.objects.filter(
                user__isnull=True,
                status='complete',
                error_message__startswith=f'GUEST_SESSION:{session_key}'
            ).order_by('-uploaded_at').first()
            
        logger.info("Guest recommendations query", extra={
            'session_key': session_key[:8] + '...' if session_key else None,
            'found_image': foot_image is not None
        })
    
    if not foot_image or foot_image.length_inches is None or foot_image.width_inches is None:
        return Response({
            'error': 'No completed foot measurement found. Please upload and process a foot image first.'
        }, status=400)
    
    user_length = foot_image.length_inches
    user_width = foot_image.width_inches
    
    # Get all active shoes
    shoes = Shoe.objects.filter(is_active=True)
    scored_shoes = []
    
    for shoe in shoes:
        # Use 4D measurements for enhanced scoring
        shoe_length, shoe_width, shoe_area, shoe_perimeter = get_real_shoe_dimensions_4d(shoe)
        
        # Use 4D scoring if foot measurements available, otherwise fallback
        if foot_image.area_sqin and foot_image.perimeter_inches:
            score = enhanced_score_shoe_4d(
                user_length, user_width, foot_image.area_sqin, foot_image.perimeter_inches,
                shoe_length, shoe_width, shoe_area, shoe_perimeter, shoe.function
            )
        else:
            # Fallback to legacy scoring for older measurements
            score = enhanced_score_shoe(user_length, user_width, shoe_length, shoe_width)
        scored_shoes.append((score, shoe))
    
    # Sort by fit score (highest first)
    scored_shoes.sort(reverse=True, key=lambda x: x[0])
    
    # Prepare response
    result = []
    for score, shoe in scored_shoes:
        data = ShoeSerializer(shoe, context={'request': request}).data
        data['fit_score'] = score
        
        # Add fit category and details for UI
        if score >= FIT_THRESHOLDS['EXCELLENT']:
            data['fit_category'] = 'Excellent'
            data['fit_details'] = 'Perfect fit with proper toe room'
        elif score >= FIT_THRESHOLDS['GOOD']:
            data['fit_category'] = 'Good'
            data['fit_details'] = 'Good fit with adequate comfort'
        elif score >= FIT_THRESHOLDS['FAIR']:
            data['fit_category'] = 'Fair'
            data['fit_details'] = 'Acceptable fit, may need consideration'
        else:
            data['fit_category'] = 'Poor'
            data['fit_details'] = 'Poor fit, not recommended'
            
        result.append(data)
    
    return Response({
        'user_measurements': {
            'length_inches': user_length,
            'width_inches': user_width,
            'area_sqin': foot_image.area_sqin,
            'perimeter_inches': foot_image.perimeter_inches
        },
        'recommendations': result,
        'total_analyzed': len(result),
        'algorithm_version': 'enhanced_4d_v2'
    })
  
@api_view(['GET'])
@permission_classes([AllowAny])
def get_latest_measurement(request):
    try:
        # Support both authenticated users and guests
        if request.user.is_authenticated:
            latest = FootImage.objects.filter(user=request.user, status='complete').order_by('-uploaded_at').first()
        else:
            # For guests, filter by session key to isolate their data
            session_key = request.session.session_key
            if not session_key:
                latest = None
            else:
                latest = FootImage.objects.filter(
                    user__isnull=True,
                    status='complete',
                    error_message__startswith=f'GUEST_SESSION:{session_key}'
                ).order_by('-uploaded_at').first()
        
        if not latest:
            return Response({"error": "No measurements found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "id": latest.id,
            "length_inches": latest.length_inches,
            "width_inches": latest.width_inches,
            "area_sqin": latest.area_sqin,
            "perimeter_inches": latest.perimeter_inches,
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
    logger.info("User account deleted successfully", extra={
        'user_id': request.user.id,
        'username': request.user.username
    })
    return Response(
        {"message": "Account deleted successfully"}, 
        status=status.HTTP_200_OK
    )
