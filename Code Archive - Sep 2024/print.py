import pandas as pd

def print_county (df, county, state, relevant_columns):
    df = df[df["State"] == state]
    df = df[df["County"] == county]

    for column in df[relevant_columns]:
        print (f"{column}: {float(df[column])}")

def print_top_scores (df, scores):
    for score in scores:
        top_counties = df.nlargest(5, score)[['NAME', 'State', score]]
        bottom_counties = df.nsmallest(5, score)[['NAME', 'State', score]]
        print (top_counties)


df = pd.read_csv("comfort_df.csv")

scores = ["temperature_score", "humidity_score", "snowfall_score", "rainfall_score", "sun_score"]
relevant_columns = ["temperature_score", "humidity_score", "rainfall_score", "snowfall_score", "sun_score", "Hottest month's avg high (F)", "Coldest month's avg high (F)", "Hottest high minus coldest high", "Hottest month's avg low (F)", "Coldest month's avg low (F)", "Annual Relative Humidity (afternoon)", "Summer Relative Humidity (afternoon)", "Hottest month's avg heat index high (F)","Annual Sunshine - Percentage of Possible","Summer Sunshine - Percentage of Possible","Winter Sunshine - Percentage of Possible","Annual rainfall (in)","Summer rainfall (in)","Winter rainfall (in)","Percent of days that include precipitation","Percent of Summer days that include precipitation","Percent of Winter days that include precipitation","Annual snowfall (in)","Days of snow per year","Average yearly windspeed (mph)","Number of days with thunder per year","Air quality Index","UV Index","Latitude","Longitude","Winter Relative Humidity (afternoon)"]
used_columns = ['Hottest month\'s avg high (F)', 'Coldest month\'s avg low (F)', 'Annual Sunshine - Percentage of Possible',
                   'Summer Relative Humidity (afternoon)', 'Winter Relative Humidity (afternoon)',
                   'Summer rainfall (in)', 'Winter rainfall (in)', 'Annual rainfall (in)',
                   'Annual snowfall (in)', 'Days of snow per year', 'UV Index']

# used_columns_plus_score = scores.extend(used_columns)

# print_county (df, "genesee", "NY", used_columns)
# print_county (df, "genesee", "NY", scores)
# print_county (df, "webster", "WV", scores)
# print_county (df, "webster", "WV", used_columns)

# print_county (df, "fauquier", "VA", scores)
# print_county (df, "fauquier", "VA", used_columns)

# print_county (df, "montgomery", "MD", scores)
# print_county (df, "montgomery", "MD", used_columns)

# print_county (df, "los angeles", "CA", used_columns)
# print_county (df, "fauquier", "VA", used_columns)

print_county (df, "cass", "ND", used_columns)

print_county (df, "knox", "ME", used_columns)
print_county (df, "freeborn", "MN", used_columns)

print_county (df, "houghton", "MI", used_columns)




# print_county (df, "montgomery", "MD", scores)
# print_county (df, "montgomery", "MD", used_columns)


# print_county (df, "orange", "CA", used_columns)
# print_county (df, "orange", "CA", scores)

# print_county (df, "carteret", "NC", scores)
# print_county (df, "carteret", "NC", used_columns)


# print_county (df, "san francisco", "CA", used_columns)
# print_county (df, "whatcom", "WA", scores)
print_top_scores(df, scores)

# print_county (df, "montgomery", "MD", ["Summer Relative Humidity (afternoon)"])

print (df["Annual Sunshine - Percentage of Possible"].describe())


print (df["Annual Sunshine - Percentage of Possible"].quantile(0.95))