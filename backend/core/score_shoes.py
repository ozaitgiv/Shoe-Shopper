import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shoe_shopper.settings')
django.setup()

from core.models import Shoe, FootImage
from core.serializers import ShoeSerializer

def score_shoe(user_length, user_width, shoe_length, shoe_width):
    # Simple scoring: penalize shoes that are too small, reward close matches
    length_diff = shoe_length - user_length
    width_diff = shoe_width - user_width
    if length_diff < 0 or width_diff < 0:
        return 0  # Shoe is too small
    # Lower difference = higher score
    score = 100 - (length_diff * 10 + width_diff * 10)
    return max(score, 0)

# Example mapping for US men's size to length in inches (approximate)
US_MENS_SIZE_TO_LENGTH = {
    7: 9.625, 7.5: 9.75, 8: 9.9375, 8.5: 10.125, 9: 10.25, 9.5: 10.4375, 10: 10.5625, 10.5: 10.75, 11: 10.9375, 11.5: 11.125, 12: 11.25
}
WIDTH_CATEGORY_TO_WIDTH = {
    'N': 3.4,  # Narrow
    'D': 3.6,  # Regular
    'W': 3.8,  # Wide
}

def get_shoe_dimensions(shoe):
    length = US_MENS_SIZE_TO_LENGTH.get(float(shoe.us_size), 10.0)  # Default to 10.0 if not found
    width = WIDTH_CATEGORY_TO_WIDTH.get(shoe.width_category, 3.6)
    return length, width

def main():
    # Get the most recent completed FootImage
    foot_image = FootImage.objects.filter(status='complete').order_by('-uploaded_at').first()
    if not foot_image or foot_image.length_inches is None or foot_image.width_inches is None:
        print("No completed foot measurement found. Please upload and process a foot image first.")
        return
    user_length = foot_image.length_inches
    user_width = foot_image.width_inches
    print(f"Using foot measurement: length={user_length} in, width={user_width} in (FootImage ID: {foot_image.id})")

    shoes = Shoe.objects.filter(is_active=True)
    scored_shoes = []
    for shoe in shoes:
        shoe_length, shoe_width = get_shoe_dimensions(shoe)
        score = score_shoe(user_length, user_width, shoe_length, shoe_width)
        scored_shoes.append((score, shoe))
    scored_shoes.sort(reverse=True, key=lambda x: x[0])
    for score, shoe in scored_shoes:
        data = ShoeSerializer(shoe).data
        data['fit_score'] = score
        print(data)

if __name__ == "__main__":
    main() 
