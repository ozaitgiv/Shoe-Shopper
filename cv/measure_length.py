import cv2
import numpy as np

# US Letter paper size in inches
PAPER_WIDTH_IN = 8.5
PAPER_HEIGHT_IN = 11.0

def is_almost_rectangle(cnt, epsilon_scale=0.03):
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, epsilon_scale * peri, True)
    return 4 <= len(approx) <= 6 and cv2.isContourConvex(approx), approx

def measure_length(image_path):
    # Validate location of the image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Image not found at {image_path}")

    # Convert image to grayscale and blur
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Morphological closing to connect gaps in edges
    kernel = np.ones((7, 7), np.uint8)
    closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    # Find all contours
    contours, _ = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Debug: Draw all large contours and print their info
    img_area = img.shape[0] * img.shape[1]
    print(f"Image area: {img_area}")
    debug_img = img.copy()
    large_contours = []
    print(f"Total contours found: {len(contours)}")
    if contours:
        largest_area = max(cv2.contourArea(cnt) for cnt in contours)
        print(f"Largest contour area: {largest_area:.0f}")
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area > 0.01 * img_area:
            is_rect, approx = is_almost_rectangle(cnt)
            color = (0, 255, 255) if is_rect else (255, 0, 255)
            cv2.drawContours(debug_img, [approx], 0, color, 2)
            print(f"Contour {i}: area={area:.0f}, points={len(approx)}, is_rect={is_rect}")
            large_contours.append((cnt, approx, is_rect, area))

    # Find the largest almost-rectangle contour (the paper)
    paper_contour = None
    paper_approx = None
    max_area = 0
    for cnt, approx, is_rect, area in large_contours:
        if is_rect and area > max_area:
            max_area = area
            paper_contour = cnt
            paper_approx = approx

    if paper_contour is None or paper_approx is None:
        print("Paper not found! Showing debug image.")
        cv2.namedWindow('Debug Large Contours', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Edges', cv2.WINDOW_NORMAL)
        def resize_for_display(image, max_w=1000, max_h=800):
            h, w = image.shape[:2]
            scale = min(max_w / w, max_h / h, 1.0)
            if scale < 1.0:
                return cv2.resize(image, (int(w * scale), int(h * scale)))
            return image
        debug_disp = resize_for_display(debug_img)
        edges_disp = resize_for_display(closed_edges)
        cv2.imshow('Debug Large Contours', debug_disp)
        cv2.imshow('Edges', edges_disp)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return

    # Create a mask for the paper area
    mask = np.zeros_like(gray)
    cv2.drawContours(mask, [paper_approx], -1, (255,), -1)

    # Mask the image so only the paper is visible
    paper_only = cv2.bitwise_and(img, img, mask=mask)
    paper_only_gray = cv2.cvtColor(paper_only, cv2.COLOR_BGR2GRAY)
    paper_only_blur = cv2.GaussianBlur(paper_only_gray, (5, 5), 0)
    paper_edges = cv2.Canny(paper_only_blur, 50, 150)

    # Find contours again, now only inside the paper
    insole_contours, _ = cv2.findContours(paper_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Find the largest contour inside the paper (the insole)
    insole_contour = None
    max_insole_area = 0
    for cnt in insole_contours:
        area = cv2.contourArea(cnt)
        if area > max_insole_area and area < 0.95 * max_area:
            max_insole_area = area
            insole_contour = cnt

    if insole_contour is None:
        print("Insole not found!")
        return

    # Draw results
    display_img = img.copy()
    cv2.drawContours(display_img, [paper_approx], 0, (0, 255, 0), 2)  # Paper in green
    cv2.drawContours(display_img, [insole_contour], 0, (0, 0, 255), 2)  # Insole in red

    # Get the min area rectangle for the insole
    insole_rect = cv2.minAreaRect(insole_contour)
    insole_box = cv2.boxPoints(insole_rect)
    insole_box = insole_box.astype(int)
    cv2.drawContours(display_img, [insole_box], 0, (255, 0, 0), 2)  # Insole bounding box in blue

    # Get the min area rectangle for the paper (for scale)
    paper_rect = cv2.minAreaRect(paper_approx)
    paper_box = cv2.boxPoints(paper_rect)
    paper_box = paper_box.astype(int)
    width_px = np.linalg.norm(paper_box[0] - paper_box[1])
    height_px = np.linalg.norm(paper_box[1] - paper_box[2])
    pixel_per_inch_w = width_px / PAPER_WIDTH_IN
    pixel_per_inch_h = height_px / PAPER_HEIGHT_IN
    pixel_per_inch = (pixel_per_inch_w + pixel_per_inch_h) / 2

    # Get insole dimensions in pixels
    insole_width_px = min(insole_rect[1])
    insole_length_px = max(insole_rect[1])

    # Convert to inches
    insole_width_in = insole_width_px / pixel_per_inch
    insole_length_in = insole_length_px / pixel_per_inch

    print(f"Insole Length: {insole_length_in:.2f} inches")
    print(f"Insole Width: {insole_width_in:.2f} inches")

    # Show the detected edges and contours
    cv2.namedWindow('Edges', cv2.WINDOW_NORMAL)
    cv2.namedWindow('Detected Contours', cv2.WINDOW_NORMAL)

    def resize_for_display(image, max_w=1000, max_h=800):
        h, w = image.shape[:2]
        scale = min(max_w / w, max_h / h, 1.0)
        if scale < 1.0:
            return cv2.resize(image, (int(w * scale), int(h * scale)))
        return image

    edges_disp = resize_for_display(paper_edges)
    display_img_disp = resize_for_display(display_img)

    cv2.imshow('Edges', edges_disp)
    cv2.imshow('Detected Contours', display_img_disp)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    measure_length("./cv/sample.jpeg")
    