import matplotlib
matplotlib.use('Agg')  # Ensures that Flask does not use GUI backend for plots

from flask import Flask, request, render_template
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import io
import base64

from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

def smart_capitalize(text):
    # Split the text into words and capitalize each one.
    # This also handles words after hyphens by splitting further by hyphen.
    return ' '.join(word.capitalize() for part in text.split() for word in part.split('-'))

def round_three(text):
    # Split the text into words and capitalize each one.
    # This also handles words after hyphens by splitting further by hyphen.
    try:
        return str(round(float(text), 3))
    except:
        return text

app = Flask(__name__)

# Register the custom filter
app.add_template_filter(smart_capitalize, 'smart_capitalize')
app.add_template_filter(round_three, 'round_three')

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

    for column in ['Hottest month\'s avg high (F)', 'Coldest month\'s avg low (F)', 'Annual Sunshine - Percentage of Possible',
                   'Summer Relative Humidity (afternoon)', 'Winter Relative Humidity (afternoon)',
                   'Summer rainfall (in)', 'Winter rainfall (in)', 'Annual rainfall (in)',
                   'Annual snowfall (in)', 'Days of snow per year', 'UV Index']:
        normalize_percentile(column)


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


    # TODO: Rename variables below such that sunshine score isn't reused, make clear the text on the website and move around to put these together
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



@app.route('/', methods=['GET', 'POST'])
def form():

    top_counties = pd.DataFrame(columns=['county_name', 'comfort_score'])
    bottom_counties = pd.DataFrame(columns=['county_name', 'comfort_score'])

    if request.method == 'POST':
        user_preferences = {
            "preferred_summer_high": float(request.form.get('preferred_summer_high', 80.0)),
            "preferred_winter_low": float(request.form.get('preferred_winter_low', 30.0)),
            # "temperature_variation_tolerance": request.form.get('temperature_variation_tolerance', 'high'),
            "preferred_summer_humidity": request.form.get('preferred_summer_humidity', 'moderate'),
            "preferred_winter_humidity": request.form.get('preferred_winter_humidity', 'high'),
            "rainfall_season_preference": request.form.get('rainfall_season_preference', 'balanced'),
            "annual_rainfall_preference": request.form.get('annual_rainfall_preference', 'moderate'),
            "enjoy_snow": request.form.get('enjoy_snow', 'yes'),
            "snow_days_preference": int(request.form.get('snow_days_preference', 10)),
            "sun_preference": request.form.get('sun_preference', 'more sun'),
            "uv_preference": request.form.get('uv_preference', 'moderate'),
            "importance_temperature": int(request.form.get('importance_temperature', 7)),
            "importance_humidity": int(request.form.get('importance_humidity', 4)),
            "importance_rainfall": int(request.form.get('importance_rainfall', 2)),
            "importance_snowfall": int(request.form.get('importance_snowfall', 2)),
            "importance_sun": int(request.form.get('importance_sun', 4))
        }

        # Load data
        merged_data = pd.read_csv("/home/mcasertano/mysite/full_df.csv")
        merged_data['geometry'] = gpd.GeoSeries.from_wkt(merged_data['geometry'])
        merged_data = gpd.GeoDataFrame(merged_data, geometry='geometry')

        # Calculate comfort score
        df_with_comfort_scores = calculate_comfort_score(merged_data, user_preferences)
        min_score = df_with_comfort_scores['comfort_score'].min()
        max_score = df_with_comfort_scores['comfort_score'].max()
        df_with_comfort_scores['normalized_score'] = (df_with_comfort_scores['comfort_score'] - min_score) / (max_score - min_score)

        top_counties = df_with_comfort_scores.nlargest(5, 'normalized_score')[['NAME', 'State', 'normalized_score']]
        bottom_counties = df_with_comfort_scores.nsmallest(5, 'normalized_score')[['NAME', 'State', 'normalized_score']]

        print (df_with_comfort_scores.head())
        print (df_with_comfort_scores["temperature_score"].mean())
        print (df_with_comfort_scores["humidity_score"].mean())
        print (df_with_comfort_scores["sun_score"].mean())
        print (df_with_comfort_scores["rainfall_score"].mean())
        print (df_with_comfort_scores["snowfall_score"].mean())
        # Plot
        fig, ax = plt.subplots()
        cmap = 'RdYlBu_r'
        df_with_comfort_scores.plot(column="normalized_score", ax=ax, cmap=cmap)
        plt.colorbar(ScalarMappable(cmap=cmap), ax=ax, shrink=0.5)
        plt.title('Your Comfort Index')

        aspect_ratio = 1.25  # For some reason, geopandas loses its ability to get the right aspect ratio when reading the file
        ax.set_aspect(aspect_ratio)

        # Encode and embed plot
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')
        plt.close(fig)

        # Render HTML with embedded plot and user preferences
        return render_template('form.html', preferences=user_preferences, plot_url=plot_url, top_counties=top_counties, bottom_counties=bottom_counties)
    else:
        # Initial GET request: load form with default values
        default_preferences = {
            "preferred_summer_high": "80.0",
            "preferred_winter_low": "30.0",
            # "temperature_variation_tolerance": "high",
            "preferred_summer_humidity": "moderate",
            "preferred_winter_humidity": "high",
            "rainfall_season_preference": "balanced",
            "annual_rainfall_preference": "moderate",
            "enjoy_snow": "yes",
            "snow_days_preference": "10",
            "sun_preference": "more sun",
            "uv_preference": "moderate",
            "importance_temperature": "7",
            "importance_humidity": "4",
            "importance_rainfall": "2",
            "importance_snowfall": "2",
            "importance_sun": "4"
        }

        return render_template('form.html', preferences=default_preferences, plot_url=None, top_counties=top_counties, bottom_counties=bottom_counties)

if __name__ == '__main__':
    app.run(debug=True)
