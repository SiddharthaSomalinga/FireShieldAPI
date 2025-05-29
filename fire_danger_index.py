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
    """
    Calculate wind factor.

    Parameters:
        wind (float): Wind speed (km/h).
        burn_index (float): Burn Index.

    Returns:
        float: Wind factor value.
    """
    if (wind >= 0) and (wind < 3):
        return burn_index + 0
    elif (wind >= 3) and (wind < 9):
        return burn_index + 5
    elif (wind >= 9) and (wind < 17):
        return burn_index + 10
    elif (wind >= 17) and (wind < 26):
        return burn_index + 15
    elif (wind >= 26) and (wind < 33):
        return burn_index + 20
    elif (wind >= 33) and (wind < 37):
        return burn_index + 25
    elif (wind >= 37) and (wind < 42):
        return burn_index + 30
    elif (wind >= 42) and (wind < 46):
        return burn_index + 35
    else:
        return burn_index + 40


def fdi(temperature, humidity, wind, days_rain, rain):
    """
    Calculate the Fire Danger Index (FDI).

    Parameters:
        temperature (float): Temperature (°C).
        humidity (float): Humidity (%).
        wind (float): Wind speed (km/h).
        days_rain (int): Days since last rain.
        rain (float): Amount of last rain (mm).

    Returns:
        int: Fire Danger Index value (rounded).

    Examples: >>> fdi(10, 50, 10, 1, 20), >>> fdi(40, 30, 30, 15, 5)
    """
    # Calculate factors
    temperature_factor = (temperature - 3) * 6.7
    humidity_factor = (90 - humidity) * 2.6

    if rain <= 0:
        rain = 1
    if days_rain <= 0:
        days_rain = 21
    if wind <= 2:
        wind = 3

    burn_factor = temperature_factor - humidity_factor
    burn_index = (burn_factor / 2 + humidity_factor) / 3.3

    wind_fac = wind_factor(wind, burn_index)

    # Initialize fdi value
    fdi_value = 0

    if (rain > 0) and (rain < 2.7):
        if days_rain == 1:
            fdi_value = wind_fac * 0.7
        elif days_rain == 2:
            fdi_value = wind_fac * 0.9
        else:
            fdi_value = wind_fac * 1
    elif (rain >= 2.7) and (rain < 5.3):
        if days_rain == 1:
            fdi_value = wind_fac * 0.6
        elif days_rain == 2:
            fdi_value = wind_fac * 0.8
        elif days_rain == 3:
            fdi_value = wind_fac * 0.9
        elif days_rain > 3:
            fdi_value = wind_fac * 1
    elif (rain >= 5.3) and (rain < 7.7):
        if days_rain == 1:
            fdi_value = wind_fac * 0.5
        elif days_rain == 2:
            fdi_value = wind_fac * 0.7
        elif days_rain == 3:
            fdi_value = wind_fac * 0.9
        elif days_rain == 4:
            fdi_value = wind_fac * 0.9
        elif days_rain > 4:
            fdi_value = wind_fac * 1
    elif (rain >= 7.7) and (rain < 10.3):
        if days_rain == 1:
            fdi_value = wind_fac * 0.4
        elif days_rain == 2:
            fdi_value = wind_fac * 0.6
        elif days_rain == 3:
            fdi_value = wind_fac * 0.8
        elif days_rain == 4:
            fdi_value = wind_fac * 0.9
        elif days_rain == 5:
            fdi_value = wind_fac * 0.9
        elif days_rain > 5:
            fdi_value = wind_fac * 1
    elif (rain >= 10.3) and (rain < 12.9):
        if days_rain == 1:
            fdi_value = wind_fac * 0.4
        elif days_rain == 2:
            fdi_value = wind_fac * 0.6
        elif days_rain == 3:
            fdi_value = wind_fac * 0.7
        elif days_rain == 4:
            fdi_value = wind_fac * 0.8
        elif days_rain == 5:
            fdi_value = wind_fac * 0.9
        elif days_rain == 6:
            fdi_value = wind_fac * 0.9
        elif days_rain > 6:
            fdi_value = wind_fac * 1
    elif (rain >= 12.9) and (rain < 15.4):
        if days_rain == 1:
            fdi_value = wind_fac * 0.3
        elif days_rain == 2:
            fdi_value = wind_fac * 0.5
        elif days_rain == 3:
            fdi_value = wind_fac * 0.7
        elif days_rain == 4:
            fdi_value = wind_fac * 0.8
        elif days_rain == 5:
            fdi_value = wind_fac * 0.8
        elif days_rain == 6:
            fdi_value = wind_fac * 0.9
        elif days_rain > 6:
            fdi_value = wind_fac * 1
    elif (rain >= 15.4) and (rain < 20.6):
        if days_rain == 1:
            fdi_value = wind_fac * 0.2
        elif days_rain == 2:
            fdi_value = wind_fac * 0.5
        elif days_rain == 3:
            fdi_value = wind_fac * 0.6
        elif days_rain == 4:
            fdi_value = wind_fac * 0.7
        elif days_rain == 5:
            fdi_value = wind_fac * 0.8
        elif days_rain == 6:
            fdi_value = wind_fac * 0.8
        elif days_rain == 7:
            fdi_value = wind_fac * 0.9
        elif days_rain == 8:
            fdi_value = wind_fac * 0.9
        elif days_rain > 8:
            fdi_value = wind_fac * 1
    elif (rain >= 20.6) and (rain < 25.6):
        if days_rain == 1:
            fdi_value = wind_fac * 0.2
        elif days_rain == 2:
            fdi_value = wind_fac * 0.4
        elif days_rain == 3:
            fdi_value = wind_fac * 0.5
        elif days_rain == 4:
            fdi_value = wind_fac * 0.7
        elif days_rain == 5:
            fdi_value = wind_fac * 0.7
        elif days_rain == 6:
            fdi_value = wind_fac * 0.8
        elif days_rain == 7:
            fdi_value = wind_fac * 0.9
        elif days_rain == 8:
            fdi_value = wind_fac * 0.9
        elif days_rain > 8:
            fdi_value = wind_fac * 1
    elif (rain >= 25.6) and (rain < 38.5):
        if days_rain == 1:
            fdi_value = wind_fac * 0.1
        elif days_rain == 2:
            fdi_value = wind_fac * 0.3
        elif days_rain == 3:
            fdi_value = wind_fac * 0.4
        elif days_rain == 4:
            fdi_value = wind_fac * 0.6
        elif days_rain == 5:
            fdi_value = wind_fac * 0.6
        elif days_rain == 6:
            fdi_value = wind_fac * 0.7
        elif days_rain == 7:
            fdi_value = wind_fac * 0.8
        elif days_rain == 8:
            fdi_value = wind_fac * 0.8
        elif days_rain == 9:
            fdi_value = wind_fac * 0.9
        elif days_rain == 10:
            fdi_value = wind_fac * 0.9
        elif days_rain > 10:
            fdi_value = wind_fac * 1
    elif (rain >= 38.5) and (rain < 51.2):
        if days_rain == 1:
            fdi_value = wind_fac * 0.0
        elif days_rain == 2:
            fdi_value = wind_fac * 0.2
        elif days_rain == 3:
            fdi_value = wind_fac * 0.4
        elif days_rain == 4:
            fdi_value = wind_fac * 0.5
        elif days_rain == 5:
            fdi_value = wind_fac * 0.5
        elif days_rain == 6:
            fdi_value = wind_fac * 0.6
        elif days_rain == 7:
            fdi_value = wind_fac * 0.7
        elif days_rain == 8:
            fdi_value = wind_fac * 0.7
        elif days_rain == 9:
            fdi_value = wind_fac * 0.8
        elif days_rain == 10:
            fdi_value = wind_fac * 0.8
        elif days_rain == 11:
            fdi_value = wind_fac * 0.9
        elif days_rain == 12:
            fdi_value = wind_fac * 0.9
        elif days_rain > 12:
            fdi_value = wind_fac * 1
    elif (rain >= 51.2) and (rain < 63.9):
        if days_rain == 1:
            fdi_value = wind_fac * 0.0
        elif days_rain == 2:
            fdi_value = wind_fac * 0.2
        elif days_rain == 3:
            fdi_value = wind_fac * 0.3
        elif days_rain == 4:
            fdi_value = wind_fac * 0.4
        elif days_rain == 5:
            fdi_value = wind_fac * 0.5
        elif days_rain == 6:
            fdi_value = wind_fac * 0.6
        elif days_rain == 7:
            fdi_value = wind_fac * 0.7
        elif days_rain == 8:
            fdi_value = wind_fac * 0.7
        elif days_rain == 9:
            fdi_value = wind_fac * 0.7
        elif days_rain == 10:
            fdi_value = wind_fac * 0.7
        elif days_rain == 11:
            fdi_value = wind_fac * 0.8
        elif days_rain == 12:
            fdi_value = wind_fac * 0.8
        elif days_rain == 13:
            fdi_value = wind_fac * 0.9
        elif days_rain == 14:
            fdi_value = wind_fac * 0.9
        elif days_rain == 15:
            fdi_value = wind_fac * 0.9
        elif days_rain > 15:
            fdi_value = wind_fac * 1
    elif (rain >= 63.9) and (rain < 76.6):
        if days_rain == 1:
            fdi_value = wind_fac * 0.0
        elif days_rain == 2:
            fdi_value = wind_fac * 0.1
        elif days_rain == 3:
            fdi_value = wind_fac * 0.2
        elif days_rain == 4:
            fdi_value = wind_fac * 0.3
        elif days_rain == 5:
            fdi_value = wind_fac * 0.4
        elif days_rain == 6:
            fdi_value = wind_fac * 0.5
        elif days_rain == 7:
            fdi_value = wind_fac * 0.6
        elif days_rain == 8:
            fdi_value = wind_fac * 0.6
        elif days_rain == 9:
            fdi_value = wind_fac * 0.7
        elif days_rain == 10:
            fdi_value = wind_fac * 0.7
        elif days_rain == 11:
            fdi_value = wind_fac * 0.8
        elif days_rain == 12:
            fdi_value = wind_fac * 0.8
        elif days_rain == 13:
            fdi_value = wind_fac * 0.8
        elif days_rain == 14:
            fdi_value = wind_fac * 0.8
        elif days_rain == 15:
            fdi_value = wind_fac * 0.8
        elif days_rain == 16:
            fdi_value = wind_fac * 0.9
        elif days_rain == 17:
            fdi_value = wind_fac * 0.9
        elif days_rain == 18:
            fdi_value = wind_fac * 0.9
        elif days_rain == 19:
            fdi_value = wind_fac * 0.9
        elif days_rain == 20:
            fdi_value = wind_fac * 0.9
        elif days_rain > 20:
            fdi_value = wind_fac * 1
    elif rain >= 76.6:
        if days_rain == 1:
            fdi_value = wind_fac * 0.0
        elif days_rain == 2:
            fdi_value = wind_fac * 0.0
        elif days_rain == 3:
            fdi_value = wind_fac * 0.1
        elif days_rain == 4:
            fdi_value = wind_fac * 0.2
        elif days_rain == 5:
            fdi_value = wind_fac * 0.4
        elif days_rain == 6:
            fdi_value = wind_fac * 0.5
        elif days_rain == 7:
            fdi_value = wind_fac * 0.6
        elif days_rain == 8:
            fdi_value = wind_fac * 0.6
        elif days_rain == 9:
            fdi_value = wind_fac * 0.6
        elif days_rain == 10:
            fdi_value = wind_fac * 0.6
        elif days_rain == 11:
            fdi_value = wind_fac * 0.7
        elif days_rain == 12:
            fdi_value = wind_fac * 0.7
        elif days_rain == 13:
            fdi_value = wind_fac * 0.8
        elif days_rain == 14:
            fdi_value = wind_fac * 0.8
        elif days_rain == 15:
            fdi_value = wind_fac * 0.8
        elif days_rain == 16:
            fdi_value = wind_fac * 0.9
        elif days_rain == 17:
            fdi_value = wind_fac * 0.9
        elif days_rain == 18:
            fdi_value = wind_fac * 0.9
        elif days_rain == 19:
            fdi_value = wind_fac * 0.9
        elif days_rain == 20:
            fdi_value = wind_fac * 0.9
        else:  # days_rain > 20
            fdi_value = wind_fac * 1

    return round(fdi_value)


# Example usage:
if __name__ == "__main__":
    # Testing the examples from the R documentation
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