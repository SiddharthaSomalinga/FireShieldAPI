import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

DATA_URL = "https://raw.githubusercontent.com/SiddharthaSomalinga/FireShield/refs/heads/main/dataset.csv"

def load_and_preprocess():
    df = pd.read_csv(DATA_URL)
    df.columns = df.columns.str.strip()
    df['Result'] = df['Result'].astype(str).str.strip().str.lower()

    features = ['Temperature', 'RH (Relative Humidity)', 'WS (Wind Speed)', 'Rain']
    target = 'Result'

    df = df.dropna(subset=[target])
    df[features] = df[features].apply(pd.to_numeric, errors='coerce')
    df[features] = df[features].fillna(df[features].mean())

    X = df[features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train_scaled, y_train)

    return model, scaler
