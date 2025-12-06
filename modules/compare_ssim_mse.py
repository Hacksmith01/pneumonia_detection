"""
modules/compare_ssim_mse.py
-----------------------------------------------------
Improved SSIM + MSE comparison for Pneumonia detection.
Now includes:
 - Median-based averaging for stability
 - Confidence margin to avoid false classifications
 - Percentage similarity display
-----------------------------------------------------
"""

import os
import random
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from modules.preprocess import preprocess_image


# Base dataset path
BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def mse(a: np.ndarray, b: np.ndarray) -> float:
    """Mean squared error."""
    return float(np.mean((a - b) ** 2))


def compare_with_dataset(uploaded_image_path: str, sample_size: int = 40, categories=("NORMAL", "PNEUMONIA")):
    uploaded = preprocess_image(uploaded_image_path)
    if uploaded is None:
        raise ValueError("❌ Uploaded image could not be preprocessed.")

    uploaded = uploaded.astype(np.float32) / 255.0
    uploaded_shape = uploaded.shape

    results_summary = {}
    best_match = {"category": None, "ssim": -1.0, "mse": float("inf"), "path": None}

    for category in categories:
        cat_dir = os.path.join(BASE_DATA_DIR, category)
        if not os.path.isdir(cat_dir):
            results_summary[category] = {"avg_ssim": None, "avg_mse": None, "samples_compared": 0}
            continue

        files = [os.path.join(cat_dir, f) for f in os.listdir(cat_dir)
                 if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        if not files:
            results_summary[category] = {"avg_ssim": None, "avg_mse": None, "samples_compared": 0}
            continue

        # Randomly sample subset for faster processing
        sampled = random.sample(files, min(sample_size, len(files)))
        ssim_scores, mse_scores = [], []

        for path in sampled:
            img = preprocess_image(path)
            if img is None:
                continue
            img = img.astype(np.float32) / 255.0
            if img.shape != uploaded_shape:
                img = cv2.resize(img, (uploaded_shape[1], uploaded_shape[0]))

            try:
                s = float(ssim(uploaded, img, data_range=1.0))
                m = mse(uploaded, img)
            except ValueError:
                continue

            ssim_scores.append(s)
            mse_scores.append(m)

            if s > best_match["ssim"]:
                best_match = {"category": category, "ssim": s, "mse": m, "path": path}

        # Use median for stability against outliers
        avg_ssim = float(np.median(ssim_scores)) if ssim_scores else None
        avg_mse = float(np.median(mse_scores)) if mse_scores else None

        results_summary[category] = {
            "avg_ssim": avg_ssim,
            "avg_mse": avg_mse,
            "samples_compared": len(ssim_scores)
        }

    # Handle missing values safely
    normal_score = results_summary.get("NORMAL", {}).get("avg_ssim") or 0.0
    pneu_score = results_summary.get("PNEUMONIA", {}).get("avg_ssim") or 0.0

    # --- Confidence margin logic ---
    diff = abs(pneu_score - normal_score)
    if diff < 0.02:
        prediction = "Uncertain Result 🤔 (SSIM scores too close)"
    elif pneu_score > normal_score:
        prediction = "Pneumonia Detected 🫁"
    else:
        prediction = "Normal Lungs ✅"

    # --- Convert to percentage for display ---
    total = normal_score + pneu_score if (normal_score + pneu_score) > 0 else 1
    normal_percent = (normal_score / total) * 100
    pneu_percent = (pneu_score / total) * 100

    return {
        "best_match": best_match if best_match["path"] else None,
        "summary": {
            "NORMAL": {
                "avg_ssim": normal_score,
                "avg_mse": results_summary.get("NORMAL", {}).get("avg_mse"),
                "similarity_percent": round(normal_percent, 2),
                "samples_compared": results_summary.get("NORMAL", {}).get("samples_compared", 0)
            },
            "PNEUMONIA": {
                "avg_ssim": pneu_score,
                "avg_mse": results_summary.get("PNEUMONIA", {}).get("avg_mse"),
                "similarity_percent": round(pneu_percent, 2),
                "samples_compared": results_summary.get("PNEUMONIA", {}).get("samples_compared", 0)
            }
        },
        "confidence_diff": round(diff, 4),
        "prediction": prediction
    }
