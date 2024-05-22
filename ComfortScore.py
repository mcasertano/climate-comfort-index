import numpy as np
import pandas as pd

# Function to calculate a comfort score
def calculate_comfort_score(df, preferences):
    
    # Define weightings based on user preferences
    weights = {
        'temperature': preferences['importance_temperature'],
        'humidity': preferences['importance_humidity'],
        'sunshine': preferences['importance_sunshine'],
        'rainfall': preferences['importance_rainfall'],
        'snowfall': preferences['importance_snowfall'],
        'uv_index': preferences['importance_uv_index']
    }
    
    # Calculate individual factor scores
    df['temperature_score'] = 1 - np.abs(df['Hottest month\'s avg high (F)'] - preferences['preferred_summer_high']) / 20
    df['temperature_score'] += 1 - np.abs(df['Coldest month\'s avg low (F)'] - preferences['preferred_winter_low']) / 15
    
    if preferences['temperature_variation_tolerance'] == 'low':
        df['temperature_score'] -= df['Hottest high minus coldest high'] / 100
    elif preferences['temperature_variation_tolerance'] == 'moderate':
        df['temperature_score'] -= df['Hottest high minus coldest high'] / 200
    else:
        df['temperature_score'] -= df['Hottest high minus coldest high'] / 300
    
    humidity_map = {'low': 0.3, 'moderate': 0.6, 'high': 1.0}
    df['humidity_score'] = 1 - np.abs(df['Summer Relative Humidity (afternoon)'] / 100 - humidity_map[preferences['preferred_summer_humidity']])
    df['humidity_score'] += 1 - np.abs(df['Winter Relative Humidity (afternoon)'] / 100 - humidity_map[preferences['preferred_winter_humidity']])

    
    df['sunshine_score'] = df['Annual Sunshine - Percentage of Possible'] / 30
    
    rainfall_map = {'low': 0.3, 'moderate': 0.6, 'high': 1.0}
    df['rainfall_score'] = 1 - np.abs(df['Annual rainfall (in)'] / 100 - rainfall_map[preferences['annual_rainfall_preference']])
    if preferences['rainfall_season_preference'] == 'summer':
        df['rainfall_score'] += df['Summer rainfall (in)'] / 100
    elif preferences['rainfall_season_preference'] == 'winter':
        df['rainfall_score'] += df['Winter rainfall (in)'] / 100
    
    df['snowfall_score'] = 1 - np.abs(df['Days of snow per year'] - preferences['snow_days_preference']) / 100
    if preferences['enjoy_snow'] == 'yes':
        df['snowfall_score'] += df['Annual snowfall (in)'] / 200
    
    uv_map = {'low': 0.3, 'moderate': 0.6, 'high': 1.0}
    df['uv_index_score'] = 1 - np.abs(df['UV Index'] / 10 - uv_map[preferences['uv_tolerance']])
    
    # Combine scores into a single comfort score
    df['comfort_score'] = (
        df['temperature_score'] * weights['temperature'] +
        df['humidity_score'] * weights['humidity'] +
        df['sunshine_score'] * weights['sunshine'] +
        df['rainfall_score'] * weights['rainfall'] +
        df['snowfall_score'] * weights['snowfall'] +
        df['uv_index_score'] * weights['uv_index']
    ) / sum(weights.values())
    
    return df