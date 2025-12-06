"""
modules/cnn_model.py
------------------------------------------------------
CNN model for Pneumonia Detection using Chest X-rays.
Includes:
 - Model architecture
 - Training pipeline
 - Prediction function
------------------------------------------------------
"""

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator, img_to_array
from PIL import Image
import numpy as np
import os


# ------------------------------------------
# 🧩 1. Build CNN Architecture
# ------------------------------------------
def build_cnn(input_shape=(128, 128, 1)):
    model = Sequential([
        Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
        MaxPooling2D(2, 2),

        Conv2D(64, (3, 3), activation='relu'),
        MaxPooling2D(2, 2),

        Conv2D(128, (3, 3), activation='relu'),
        MaxPooling2D(2, 2),

        Flatten(),
        Dense(128, activation='relu'),
        Dropout(0.3),
        Dense(1, activation='sigmoid')  # Output: 1 neuron (binary classification)
    ])

    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model


# ------------------------------------------
# 🏋️‍♂️ 2. Training Function
# ------------------------------------------
def train_cnn_model(data_dir="data", img_size=(128, 128), batch_size=16, epochs=5):
    """
    Train CNN on your chest X-ray dataset.
    Dataset structure:
    data/
      ├── NORMAL/
      └── PNEUMONIA/
    """
    train_datagen = ImageDataGenerator(
        rescale=1.0/255,
        validation_split=0.2,
        zoom_range=0.1,
        rotation_range=15,
        horizontal_flip=True
    )

    train_gen = train_datagen.flow_from_directory(
        data_dir,
        target_size=img_size,
        color_mode="grayscale",
        class_mode="binary",
        batch_size=batch_size,
        subset="training"
    )

    val_gen = train_datagen.flow_from_directory(
        data_dir,
        target_size=img_size,
        color_mode="grayscale",
        class_mode="binary",
        batch_size=batch_size,
        subset="validation"
    )

    model = build_cnn(input_shape=(img_size[0], img_size[1], 1))

    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=epochs
    )

    model.save("pneumonia_cnn_model.h5")
    print("✅ Model trained and saved as pneumonia_cnn_model.h5")
    return history


# ------------------------------------------
# 🔮 3. Prediction Function
# ------------------------------------------
def predict_image(model_path, image_path):
    """
    Load the trained CNN model and predict whether the image shows pneumonia.
    """
    import numpy as np
    from tensorflow.keras.preprocessing.image import load_img, img_to_array
    import tensorflow as tf

    model = tf.keras.models.load_model(model_path)

    # Load & normalize image
    img = load_img(image_path, color_mode="grayscale", target_size=(128, 128))
    img_array = img_to_array(img) / 255.0           # ensure range [0,1]
    img_array = np.expand_dims(img_array, axis=0)

    # Get prediction
    pred = float(model.predict(img_array)[0][0])

    # Clamp prediction between 0 and 1
    pred = max(0.0, min(1.0, pred))

    if pred > 0.5:
        confidence = round(pred * 100, 2)
        label = "Pneumonia Detected 🫁"
    else:
        confidence = round((1 - pred) * 100, 2)
        label = "Normal Lungs ✅"

    return confidence, label