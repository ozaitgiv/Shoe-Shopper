import cv2
import numpy as np

def measure_length(image_path):

    # Validate location of the image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Image not found at {image_path}")

    # Convert image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Edge detection
    edges = cv2.Canny(gray, 50, 150)
    # Find countours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Desired maximum display dimensions
    max_display_width = 1000
    max_display_height = 800

    # Compute scaling factors
    height, width = img.shape[:2]
    scale_w = max_display_width / width
    scale_h = max_display_height / height
    scale = min(scale_w, scale_h, 1.0)  # Do not upscale if image is smaller

    # Compute new dimensions
    new_width = int(width * scale)
    new_height = int(height * scale)

    # Resize
    resized_img = cv2.resize(img, (new_width, new_height))

    # Temp
    cv2.imshow('Original', resized_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    measure_length("sample.jpeg")

