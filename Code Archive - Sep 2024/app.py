import matplotlib
matplotlib.use('Agg')  # Ensures that Flask does not use GUI backend for plots

from flask import Flask, request, render_template
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import io
import base64
from ComfortScore2 import calculate_comfort_score

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
        merged_data = pd.read_csv("full_df.csv")
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
