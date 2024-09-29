import numpy as np
import pandas as pd

# Function to calculate a comfort score
def calculate_comfort_score(df, preferences):
    
    # Define weightings based on user preferences
    weights = {
        'temperature': preferences['importance_temperature'],
        'humidity': preferences['importance_humidity'],
        'sun': preferences['importance_sun'],
        'rainfall': preferences['importance_rainfall'],
        'snowfall': preferences['importance_snowfall'],
    }

    # Percentile-based normalization, converts all columns to be between 0 and 1 with thresholds set at the 5th and 95th percentiles
    def normalize_percentile(column):
        lower = df[column].quantile(0.05)
        upper = df[column].quantile(0.95)
        df[column + '_normalized'] = (df[column] - lower) / (upper - lower)
        df[column + '_normalized'] = df[column + '_normalized'].clip(0, 1)

    # Calculate individual factor scores using normalized data
    df['hot_temperature_score'] = -np.abs(df['Hottest month\'s avg high (F)'] - preferences['preferred_summer_high'])
    normalize_percentile("hot_temperature_score")

    df["cold_temperature_score"] = -np.abs(df['Coldest month\'s avg low (F)'] - preferences['preferred_winter_low'])
    normalize_percentile("cold_temperature_score")

    df['temperature_score'] = df["hot_temperature_score_normalized"] + df["cold_temperature_score_normalized"]
    
    # TODO: TEMPERATURE VARIATION

    # if preferences['temperature_variation_tolerance'] == 'low':
    #     df['temperature_score'] -= (df['Hottest month\'s avg high (F)'] - df['Coldest month\'s avg low (F)']).abs() / 100
    # elif preferences['temperature_variation_tolerance'] == 'moderate':
    #     df['temperature_score'] -= (df['Hottest month\'s avg high (F)'] - df['Coldest month\'s avg low (F)']).abs() / 200
    # else:
    #     df['temperature_score'] -= (df['Hottest month\'s avg high (F)'] - df['Coldest month\'s avg low (F)']).abs() / 300

    # Map user preferences to normalized values

    ### Humidity

    summer_humidity_map = {'low': df['Summer Relative Humidity (afternoon)'].min(), 'moderate': df['Summer Relative Humidity (afternoon)'].mean(), 'high': df['Summer Relative Humidity (afternoon)'].max()}
    df['summer_humidity_score'] = -np.abs(df['Summer Relative Humidity (afternoon)'] - summer_humidity_map[preferences['preferred_summer_humidity']])
    normalize_percentile("summer_humidity_score")

    winter_humidity_map = {'low': df['Winter Relative Humidity (afternoon)'].min(), 'moderate': df['Winter Relative Humidity (afternoon)'].mean(), 'high': df['Winter Relative Humidity (afternoon)'].max()}
    df['winter_humidity_score'] = -np.abs(df['Winter Relative Humidity (afternoon)'] - winter_humidity_map[preferences['preferred_winter_humidity']])
    normalize_percentile("winter_humidity_score")

    df['humidity_score'] = df["summer_humidity_score_normalized"] + df["winter_humidity_score_normalized"]


    ### Rainfall

    winter_humidity_map = {'low': df['Winter Relative Humidity (afternoon)'].min(), 'moderate': df['Winter Relative Humidity (afternoon)'].mean(), 'high': df['Winter Relative Humidity (afternoon)'].max()}
    
    rainfall_map = {'low': df['Annual rainfall (in)'].min(), 'moderate': df['Annual rainfall (in)'].mean(), 'high': df['Annual rainfall (in)'].max()}
    df['annual_rainfall_score'] = -np.abs(df['Annual rainfall (in)'] - rainfall_map[preferences['annual_rainfall_preference']])
    normalize_percentile('annual_rainfall_score')

    df['rainfall_difference'] = df['Summer rainfall (in)'] - df['Winter rainfall (in)']
    if preferences['rainfall_season_preference'] == 'balanced':
        df['rainfall_diff_score'] = -np.abs(df['rainfall_difference'])
    elif preferences['rainfall_season_preference'] == 'more in summer':
        df['rainfall_diff_score'] = df['rainfall_difference']
    elif preferences['rainfall_season_preference'] == 'more in winter':
        df['rainfall_diff_score'] = -df['rainfall_difference']
    else:
        df['rainfall_diff_score'] = df['annual_rainfall_score']
        raise Exception ("Unknown rainfall season preference")
    normalize_percentile('rainfall_diff_score')

    
    df["rainfall_score"] = df["annual_rainfall_score_normalized"] + df["rainfall_diff_score_normalized"]


    ### Snowfall


    df['snowfall_score_days'] = 1 - np.abs(df['Days of snow per year'] - preferences['snow_days_preference'])
    normalize_percentile("snowfall_score_days")

    if preferences['enjoy_snow'] == 'yes':
        df['snowfall_score_inches'] = df['Annual snowfall (in)']
        normalize_percentile("snowfall_score_inches")
    else:
        df['snowfall_score_inches'] = -df['Annual snowfall (in)']
        normalize_percentile("snowfall_score_inches")


    df["snowfall_score"] = df["snowfall_score_days_normalized"] + df["snowfall_score_inches_normalized"]


    ### Sunshine

    sunshine_map = {'less sun': df['Annual Sunshine - Percentage of Possible'].min(), 'average sun': df['Annual Sunshine - Percentage of Possible'].mean(), 'more sun': df['Annual Sunshine - Percentage of Possible'].max()}
    df['sunshine_score'] = -np.abs(df['Annual Sunshine - Percentage of Possible'] - sunshine_map[preferences['sun_preference']])
    normalize_percentile("sunshine_score")

    uv_map = {'low': df['UV Index'].min(), 'moderate': df['UV Index'].mean(), 'high': df['UV Index'].max()}
    df['uv_index_score'] = -np.abs(df['UV Index'] - uv_map[preferences['uv_preference']])
    normalize_percentile("uv_index_score")

    df['sun_score'] = df["sunshine_score_normalized"] + df["uv_index_score_normalized"]

    # Combine scores into a single comfort score
    df['comfort_score'] = (
        df['temperature_score'] * weights['temperature'] +
        df['humidity_score'] * weights['humidity'] +
        df['rainfall_score'] * weights['rainfall'] +
        df['snowfall_score'] * weights['snowfall'] +
        df['sun_score'] * weights['sun']
    ) / sum(weights.values())

    df.to_csv("comfort_df.csv")

    return df