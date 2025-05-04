from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
from data_loader import load_and_preprocess

app = FastAPI()

# Load model and scaler at startup
model, scaler = load_and_preprocess()

class Features(BaseModel):
    Temperature: float
    RH: float
    WS: float
    Rain: float

@app.post("/predict")
def predict_fire(data: Features):
    input_array = np.array([[data.Temperature, data.RH, data.WS, data.Rain]])
    scaled = scaler.transform(input_array)
    probs = model.predict_proba(scaled)[0]
    labels = model.classes_

    prob_fire = sum(probs[i] for i, label in enumerate(labels) if label.strip() == "fire")
    prob_no_fire = sum(probs[i] for i, label in enumerate(labels) if label.strip() == "not fire")

    prediction = "fire" if prob_fire > prob_no_fire else "not fire"
    return {
        "prediction": prediction,
        "probabilities": {
            "fire": round(prob_fire * 100, 2),
            "not_fire": round(prob_no_fire * 100, 2)
        }
    }
