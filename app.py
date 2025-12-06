import os
import random
import json
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, send_file, jsonify, session
from werkzeug.utils import secure_filename
from modules.compare_ssim_mse import compare_with_dataset

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception as e:
    print(f"⚠️ Warning: Could not load .env file: {e}")
    print("   You can set GEMINI_API_KEY as an environment variable instead.")
# optional CNN (only used if model exists)
try:
    from modules.cnn_model import predict_image
    HAVE_CNN = True
except Exception:
    HAVE_CNN = False

# optional Gemini (only used if available)
try:
    from modules.gemini_api import analyze_xray_image, chat_with_gemini, GEMINI_AVAILABLE
    HAVE_GEMINI = GEMINI_AVAILABLE
except Exception:
    HAVE_GEMINI = False

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = "replace-with-a-secure-secret"  # change in production
app.config['SESSION_TYPE'] = 'filesystem'


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/data/<category>/<filename>")
def dataset_file(category, filename):
    return send_from_directory(os.path.join("data", category), filename)


@app.route("/sample-image")
def sample_image():
    """Return a random sample image from the dataset for testing."""
    categories = ["NORMAL", "PNEUMONIA"]
    category = random.choice(categories)
    cat_dir = os.path.join(DATA_DIR, category)
    
    if os.path.isdir(cat_dir):
        files = [f for f in os.listdir(cat_dir) 
                if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        if files:
            filename = random.choice(files)
            return send_from_directory(cat_dir, filename)
    
    flash("No sample images available")
    return redirect(url_for("index"))


@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        flash("No file part")
        return redirect(url_for("index"))

    file = request.files["file"]
    if file.filename == "":
        flash("No selected file")
        return redirect(url_for("index"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        saved_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(saved_path)

        # Run SSIM/MSE comparison
        try:
            results = compare_with_dataset(saved_path, sample_size=40)
        except Exception as e:
            flash(f"Error during SSIM comparison: {e}")
            return redirect(url_for("index"))

        # CNN confirm (optional)
        cnn_info = None
        if HAVE_CNN and os.path.exists(os.path.join(BASE_DIR, "pneumonia_cnn_model.h5")):
            try:
                confidence, cnn_label = predict_image("pneumonia_cnn_model.h5", saved_path)
                cnn_info = {"confidence": confidence, "label": cnn_label}
            except Exception as e:
                cnn_info = {"error": str(e)}

        # Prepare data for template (safe types)
        best_match = results.get("best_match")
        summary = results.get("summary", {})
        prediction = results.get("prediction", "Unknown")
        confidence_diff = results.get("confidence_diff", None)

        # Compare CNN and SSIM/MSE results
        mismatch_warning = None
        if cnn_info and not cnn_info.get("error"):
            cnn_label = cnn_info.get("label", "")
            ssim_pred = prediction
            
            # Check if predictions match
            cnn_is_pneumonia = "Pneumonia" in cnn_label
            ssim_is_pneumonia = "Pneumonia" in ssim_pred
            
            if cnn_is_pneumonia != ssim_is_pneumonia:
                mismatch_warning = {
                    "message": "⚠️ Results Mismatch Detected",
                    "details": "The CNN model and SSIM/MSE comparison produced different results. The CNN prediction is generally more reliable as it's trained on a large dataset, but we recommend taking precautions and consulting with a medical professional for a definitive diagnosis.",
                    "cnn_preferred": True
                }
            elif "Uncertain" in ssim_pred:
                mismatch_warning = {
                    "message": "⚠️ Uncertain SSIM/MSE Result",
                    "details": "The SSIM/MSE comparison showed uncertain results, but the CNN model provided a clear prediction. The CNN result is preferred in this case.",
                    "cnn_preferred": True
                }

        # Gemini analysis (optional)
        gemini_analysis = None
        if HAVE_GEMINI:
            try:
                gemini_analysis = analyze_xray_image(
                    saved_path,
                    {"prediction": prediction, "summary": summary, "confidence_diff": confidence_diff},
                    cnn_info
                )
            except Exception as e:
                print(f"Gemini analysis error: {e}")
                gemini_analysis = None

        # Store image path in session for chat functionality
        session['current_image_path'] = saved_path
        session['conversation_history'] = []

        return render_template(
            "result.html",
            upload_url=url_for("uploaded_file", filename=filename),
            best_match_path=(url_for("dataset_file",
                         category=best_match["category"],
                         filename=os.path.basename(best_match["path"]))
                 if best_match else None),
            best_match_info=best_match,
            summary=summary,
            prediction=prediction,
            confidence_diff=confidence_diff,
            cnn_info=cnn_info,
            mismatch_warning=mismatch_warning,
            gemini_analysis=gemini_analysis,
            gemini_available=HAVE_GEMINI
        )

    else:
        flash("Unsupported file type")
        return redirect(url_for("index"))


@app.route("/api/chat", methods=["POST"])
def gemini_chat():
    """Handle chat messages with Gemini about the uploaded image."""
    if not HAVE_GEMINI:
        return jsonify({"error": "Gemini API not available"}), 503
    
    data = request.get_json()
    message = data.get("message", "").strip()
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    # Get image path from session
    image_path = session.get('current_image_path')
    if not image_path or not os.path.exists(image_path):
        return jsonify({"error": "No image available for chat"}), 400
    
    # Get conversation history
    conversation_history = session.get('conversation_history', [])
    
    try:
        # Get response from Gemini
        response = chat_with_gemini(message, image_path, conversation_history)
        
        if response:
            # Update conversation history
            conversation_history.append({"role": "user", "content": message})
            conversation_history.append({"role": "assistant", "content": response})
            session['conversation_history'] = conversation_history[-10:]  # Keep last 10 messages
            
            return jsonify({"response": response})
        else:
            return jsonify({"error": "Failed to get response from Gemini"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
