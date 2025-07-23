# backend/test_recommendations.py
"""
Test the current recommendation system to see what algorithm it's using
"""
import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shoe_shopper.settings')
django.setup()

from core.models import Shoe, FootImage
from core.views import score_shoe, get_shoe_dimensions

def test_current_algorithm():
    """Test what the current algorithm is doing"""
    print("=== TESTING CURRENT RECOMMENDATION ALGORITHM ===\n")
    
    # Get all shoes
    shoes = Shoe.objects.filter(is_active=True)
    print(f"Total shoes in database: {shoes.count()}\n")
    
    # Check how many have real insole measurements
    with_measurements = shoes.filter(
        insole_length__isnull=False,
        insole_width__isnull=False
    ).count()
    print(f"Shoes with real insole measurements: {with_measurements}/{shoes.count()}")
    
    # Simulate a user measurement (typical foot size)
    test_user_length = 10.5  # inches
    test_user_width = 4.0    # inches
    print(f"\nTest user measurements: {test_user_length}\" x {test_user_width}\"\n")
    
    print("=== CURRENT ALGORITHM BEHAVIOR ===")
    print("Shoe | Real Insole Data | Algorithm Uses | Fit Score")
    print("-" * 65)
    
    for shoe in shoes[:5]:  # Test first 5 shoes
        # What the current algorithm does
        algo_length, algo_width = get_shoe_dimensions(shoe)
        fit_score = score_shoe(test_user_length, test_user_width, algo_length, algo_width)
        
        # What we COULD do with real data
        real_length = shoe.insole_length or "None"
        real_width = shoe.insole_width or "None"
        
        print(f"{shoe.company[:8]:8} | {real_length:4} x {real_width:4} | {algo_length:4.1f} x {algo_width:4.1f} | {fit_score:3.0f}")
    
    print(f"\n=== THE PROBLEM ===")
    print("Current algorithm uses STATIC size mappings instead of REAL insole measurements")
    print("Frontend uses MOCK data instead of backend API")
    
    print(f"\n=== THE SOLUTION ===")
    print("Step 1: Update algorithm to use real insole measurements")
    print("Step 2: Connect frontend to real backend data")
    
def check_api_endpoint():
    """Check what the /api/recommendations/ endpoint returns"""
    print("\n=== CHECKING API ENDPOINT ===")
    
    # Check if we have any completed foot measurements
    foot_images = FootImage.objects.filter(status='complete')
    if foot_images.exists():
        latest = foot_images.order_by('-uploaded_at').first()
        print(f"Latest foot measurement: {latest.length_inches}\" x {latest.width_inches}\"")
        print("API endpoint would work")
    else:
        print("No completed foot measurements - API would return error")
        print("Need to upload a foot image first or create test data")

if __name__ == "__main__":
    test_current_algorithm()
    check_api_endpoint()