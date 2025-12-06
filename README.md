# Pneumonia Detection Web App

## Project Overview

This project is a web application for detecting pneumonia from chest X-ray images.  
It uses a Convolutional Neural Network (CNN) to classify X-ray images into categories such as “Normal” or “Pneumonia (Bacterial/Viral)”.  
The application backend is written in Python (Flask), and provides a simple web interface to upload an X-ray image and get a prediction.

## Dataset

The dataset used here is **“Chest X-Ray Images (Pneumonia)”** from Kaggle:  
[https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia](https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia)

**Important:**  
- The dataset is _not included_ in this repository due to large size.  
- After downloading, create the following folder structure at the project root:

```
data/
  ├── PNEUMONIA/
  └── NORMAL/
```

- Place the respective chest-X-ray images into `data/PNEUMONIA/` (pneumonia cases) and `data/NORMAL/` (healthy cases).

## Project Structure

```
.
├── app.py                      # Flask backend
├── modules/                    # Supporting modules for ML, preprocessing, etc.
│   ├── cnn_model.py
│   ├── preprocess.py
│   ├── compare_ssim_mse.py
│   └── gemini_api.py           # (if using external API; optional)
├── static/                     # Static files (CSS, JS)
│   ├── styles.css
│   └── scripts.js
├── templates/                  # HTML templates for web interface
│   ├── index.html
│   ├── result.html
│   └── medlogo.png             # Logo or icon (optional)
├── requirements.txt            # Project dependencies
└── README.md                   # This file
```

## Setup & Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Hacksmith01/pneumonia_detection.git
   cd pneumonia_detection
   ```

2. (Recommended) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate     # On Linux / macOS
   .\\venv\\Scripts\\activate    # On Windows (PowerShell / CMD)
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Download the dataset from Kaggle and set up the folder structure as shown above.

5. Run the Flask app:
   ```bash
   python app.py
   ```

6. Open a browser and navigate to `http://localhost:5000` to view the web UI.

## Usage

- On the web UI — upload a chest X-ray image (JPEG/PNG).  
- The app will process the image, run the trained CNN model, and display a diagnosis: either “Normal” or “Pneumonia”.  
- (Optional) You can add more options: e.g. show confidence/score, allow multiple images, download result, etc.

## Notes & Best Practices

- Since the dataset is large, do **not** upload the entire dataset to GitHub.  
- Maintain data privacy — do not commit patient or sensitive data.  
- Use `.gitignore` to exclude environment folders (`venv/`, `.tfenv/`), logs, raw datasets, model binaries.  
- For reproducibility, consistently use the same preprocessing, image resizing, and model hyperparameters.

## Contributing

If you plan to improve this project (better model, web UI, API endpoint, etc.):

- Fork the repo  
- Create a new branch (e.g. `dev/feature-name`)  
- Write clear commit messages  
- Submit a Pull Request with description of changes  

## License

This project is for educational/research purposes.  
If you redistribute or publish your own derivative work, please give proper credit to the original dataset and this repository.

