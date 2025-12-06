import cv2
import numpy as np

def preprocess_image(image_path):
    """
    Preprocess an X-ray image for consistency:
    1. Convert to grayscale
    2. Resize to (512x512)
    3. Normalize brightness/contrast
    4. Apply CLAHE (contrast enhancement)
    5. Gaussian blur for denoising
    """
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None

        img = cv2.resize(img, (512, 512), interpolation=cv2.INTER_AREA)
        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img = clahe.apply(img)

        img = cv2.GaussianBlur(img, (3, 3), 0)

        return img
    except Exception as e:
        print(f"Preprocessing error for {image_path}: {e}")
        return None
