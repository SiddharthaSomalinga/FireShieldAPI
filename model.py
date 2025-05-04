import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from typing import Tuple

class ForestFireModel:
    def __init__(self, data_url: str):
        self.data_url = data_url
        self.features = ['Temperature', 'RH (Relative Humidity)', 'WS (Wind Speed)', 'Rain']
        self.target_column = 'Result'
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()

    def load_data(self) -> pd.DataFrame:
        df = pd.read_csv(self.data_url)
        df.columns = df.columns.str.strip()

        # Clean target
        df[self.target_column] = df[self.target_column].astype(str).str.strip().str.lower()
        df = df.dropna(subset=[self.target_column])

        # Convert to numeric
        df[self.features] = df[self.features].apply(pd.to_numeric, errors='coerce')
        df[self.features] = df[self.features].fillna(df[self.features].mean())

        return df

    def train(self) -> None:
        df = self.load_data()
        X = df[self.features]
        y = df[self.target_column]

        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)

        X_train_scaled = self.scaler.fit_transform(X_train)
        self.model.fit(X_train_scaled, y_train)

    def predict(self, input_data: list) -> Tuple[str, float, float]:
        input_array = np.array([input_data])
        scaled = self.scaler.transform(input_array)
        probs = self.model.predict_proba(scaled)[0]
        labels = self.model.classes_

        prob_fire = sum(probs[i] for i, label in enumerate(labels) if label.strip() == "fire")
        prob_no_fire = sum(probs[i] for i, label in enumerate(labels) if label.strip() == "not fire")
        prediction = "fire" if prob_fire > prob_no_fire else "not fire"

        return prediction, prob_fire * 100, prob_no_fire * 100
