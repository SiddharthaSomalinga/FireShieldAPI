import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from datetime import datetime, timezone

# Setup caching and retries
cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# CONFIG: Replace with any city's coordinates
latitude = 33.1507
longitude = -96.8236

# Use a reasonable lookback period (e.g., 90 days)
end_date = datetime.now().date()
start_date = (end_date - pd.Timedelta(days=90)).strftime("%Y-%m-%d")

# Request hourly rain data
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

# Extract hourly rain data
hourly = response.Hourly()
rain = hourly.Variables(0).ValuesAsNumpy()
timestamps = pd.date_range(
    start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
    end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
    freq=pd.Timedelta(seconds=hourly.Interval()),
    inclusive="left"
)

# Create DataFrame and resample to daily rainfall totals
df = pd.DataFrame({"datetime": timestamps, "rain": rain})
df = df.set_index("datetime").resample("D").sum()

# Find last rainy day
rainy_days = df[df["rain"] > 0]
if rainy_days.empty:
    print("No rain in the past 90 days.")
else:
    last_rain_date = rainy_days.index[-1].date()
    rainfall_on_last_rain = rainy_days.iloc[-1]["rain"]
    days_since_last_rain = (datetime.now(timezone.utc).date() - last_rain_date).days

    print(f"Last rain: {last_rain_date}")
    print(f"Rainfall on that day: {rainfall_on_last_rain:.2f} mm")
    print(f"Days since last rain: {days_since_last_rain}")
