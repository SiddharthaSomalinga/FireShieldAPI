import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from datetime import datetime, timezone

def get_days_since_last_rain(latitude: float, longitude: float, lookback_days: int = 90):
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    end_date = datetime.now().date()
    start_date = (end_date - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date.strftime("%Y-%m-%d"),
        "hourly": "rain"
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    hourly = response.Hourly()
    rain = hourly.Variables(0).ValuesAsNumpy()
    timestamps = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )

    df = pd.DataFrame({"datetime": timestamps, "rain": rain})
    df = df.set_index("datetime").resample("D").sum()

    rainy_days = df[df["rain"] > 0]
    if rainy_days.empty:
        return None, None, lookback_days
    else:
        last_rain_date = rainy_days.index[-1].date()
        rainfall_on_last_rain = rainy_days.iloc[-1]["rain"]
        days_since_last_rain = (datetime.now(timezone.utc).date() - last_rain_date).days
        return last_rain_date, rainfall_on_last_rain, days_since_last_rain

def wind_factor(wind, burn_index):
    for threshold, add in zip([3, 9, 17, 26, 33, 37, 42, 46], [0, 5, 10, 15, 20, 25, 30, 35]):
        if wind < threshold:
            return burn_index + add
    return burn_index + 40

def get_adjustment_factor(rain, days_rain):
    # Lookup table for (rain_range, max_days, multipliers)
    thresholds = [
        (0, 2.7,   [0.7, 0.9, 1.0]),
        (2.7, 5.3, [0.6, 0.8, 0.9, 1.0]),
        (5.3, 7.7, [0.5, 0.7, 0.9, 0.9, 1.0]),
        (7.7, 10.3,[0.4, 0.6, 0.8, 0.9, 0.9, 1.0]),
        (10.3, 12.9,[0.4, 0.6, 0.7, 0.8, 0.9, 0.9, 1.0]),
        (12.9, 15.4,[0.3, 0.5, 0.7, 0.8, 0.8, 0.9, 1.0]),
        (15.4, 20.6,[0.2, 0.5, 0.6, 0.7, 0.8, 0.8, 0.9, 0.9, 1.0]),
        (20.6, 25.6,[0.2, 0.4, 0.5, 0.7, 0.7, 0.8, 0.9, 0.9, 1.0]),
        (25.6, 38.5,[0.1, 0.3, 0.4, 0.6, 0.6, 0.7, 0.8, 0.8, 0.9, 0.9, 1.0]),
        (38.5, 51.2,[0.0, 0.2, 0.4, 0.5, 0.5, 0.6, 0.7, 0.7, 0.8, 0.8, 0.9, 0.9, 1.0]),
        (51.2, 63.9,[0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.7, 0.7, 0.7, 0.8, 0.8, 0.9, 0.9, 0.9, 1.0]),
        (63.9, 76.6,[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.6, 0.7, 0.7, 0.8, 0.8, 0.8, 0.8, 0.8, 0.9, 0.9, 0.9, 0.9, 0.9, 1.0]),
        (76.6, float("inf"), [0.0, 0.0, 0.1, 0.2, 0.4, 0.5, 0.6, 0.6, 0.6, 0.6, 0.7, 0.7, 0.8, 0.8, 0.8, 0.9, 0.9, 0.9, 0.9, 0.9, 1.0])
    ]

    for low, high, factors in thresholds:
        if low <= rain < high:
            index = min(days_rain - 1, len(factors) - 1)
            return factors[index]
    return 1.0

def fdi(temperature, humidity, wind, days_rain, rain):
    temperature_factor = (temperature - 3) * 6.7
    humidity_factor = (90 - humidity) * 2.6

    rain = max(rain, 1)
    days_rain = max(days_rain, 1)
    wind = max(wind, 3)

    burn_factor = temperature_factor - humidity_factor
    burn_index = (burn_factor / 2 + humidity_factor) / 3.3
    wind_fac = wind_factor(wind, burn_index)

    adjustment = get_adjustment_factor(rain, days_rain)
    return round(wind_fac * adjustment)

# Example usage:
if __name__ == "__main__":
    # The Fire Danger Index (FDI) uses 5 categories to rate the fire danger represented by colour codes [Blue (insignificant) (0-20), Green (low) (21-45), Yellow (moderate) (46-60), Orange (high) (61-75) and Red (extremely high) (75<)]. Each of the danger rating is accompanied by precaution statement.
    latitude = 33.1507
    longitude = -96.8236

    # Step 1: Get rain history data
    last_rain_date, rainfall_amount, days_since_rain = get_days_since_last_rain(latitude, longitude)
    print(f"Last Rain Date: {last_rain_date}")
    print(f"Rainfall Amount on that day: {rainfall_amount} mm")
    print(f"Days Since Last Rain: {days_since_rain}")

    # Order of variables for fdi function: temperature, humidity, wind speed, days_since_rain, rainfall_amount
    print(fdi(10, 50, 10, days_since_rain, rainfall_amount))  # Example 1
    print(fdi(40, 30, 30, days_since_rain, rainfall_amount))  # Example 2