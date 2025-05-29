import coremltools as ct
import numpy as np

# Load the model
model = ct.models.MLModel("FirePredictor.mlmodel")

# Prepare input dict matching your input feature names and types
input_data = {
    "Temperature": 34.0,
    "RH (Relative Humidity)": 2.0,
    "WS (Wind Speed)": 10.0,
    "Rain": 0.0
}

# Run prediction
prediction = model.predict(input_data)

print(prediction)
