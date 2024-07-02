import os
import pandas as pd
import requests
from io import StringIO

def fetch_and_clean_data():
    # Constant variables
    DATA_DIR = 'data'
    POP_THRESHOLD = 1000000
    EXCLUDE_LOCATIONS = ['World', 'Africa', 'Asia', 'Oceania', 'Europe', 'European Union', 'South America', 'North America', 'Low income', 'Lower middle income', 'Upper middle income', 'High income']
    COLS_TO_CLEAN = ['excess_mortality', 'excess_mortality_cumulative', 'excess_mortality_cumulative_absolute', 'excess_mortality_cumulative_per_million']
    COVID_COLUMNS = ['location', 'date', 'new_cases', 'new_deaths', 'total_cases_per_million', 'total_deaths_per_million'] + COLS_TO_CLEAN
    
    # Fetch the OWID COVID-19 data
    url = 'https://github.com/owid/covid-19-data/raw/master/public/data/owid-covid-data.csv'
    response = requests.get(url)
    owid_covid = pd.read_csv(StringIO(response.text))

    # Read additional datasets
    additional_files = [
        'changes-residential-duration-covid.csv',
        'covid-19-testing-policy.csv',
        'covid-contact-tracing.csv',
        'covid-containment-and-health-index.csv',
        'covid-vaccination-policy.csv',
        'face-covering-policies-covid.csv',
        'internal-movement-covid.csv',
        'international-travel-covid.csv',
        'public-events-covid.csv',
        'public-gathering-rules-covid.csv',
        'public-transport-covid.csv',
        'school-closures-covid.csv',
        'stay-at-home-covid.csv',
        'workplace-closures-covid.csv'
    ]

    dfdict = {}
    for file in additional_files:
        name = file.split('-covid')[0].replace('-', '_')  # Extract name from file path
        dfdict[name] = pd.read_csv(os.path.join(DATA_DIR, file))

    # Select columns from OWID data
    covid = owid_covid[COVID_COLUMNS]

    # Filter by population and exclude certain locations
    covid = covid.loc[
        (owid_covid.population >= POP_THRESHOLD) & \
        (~owid_covid.location.isin(EXCLUDE_LOCATIONS))
    ]

    # Merge additional datasets
    for _, df in dfdict.items():
        covid = pd.merge(covid, df, how='left', left_on=['location', 'date'], right_on=['Entity', 'Day'])
        covid.drop(['Entity', 'Code', 'Day'], axis=1, inplace=True)

    # Function to fill in sparse data for select columns
    def clean_column(column):
        return covid.groupby('location')[column].ffill()

    # Clean the merged data
    covid['date'] = pd.to_datetime(covid['date'])
    for col in COLS_TO_CLEAN:
        covid[col] = clean_column(col) 
    
    # Backfilling for new_cases and new_deaths
    covid['new_cases'] = covid.groupby('location')['new_cases'].bfill()
    covid['new_deaths'] = covid.groupby('location')['new_deaths'].bfill()
    
    # Define the window size for smoothing 7 days 
    smoothing_window = 7
    
    # Smoothed columns using rolling average
    covid['new_cases_smoothed'] = covid.groupby('location')['new_cases'].rolling(window=smoothing_window, min_periods=1).mean().reset_index(level=0, drop=True)
    covid['new_deaths_smoothed'] = covid.groupby('location')['new_deaths'].rolling(window=smoothing_window, min_periods=1).mean().reset_index(level=0, drop=True)
    
    covid.sort_values(by=['location', 'date'], inplace=True)

    # Save the cleaned data to a CSV file
    cleaned_file_path = os.path.join(DATA_DIR, 'owid-covid-data-cleaned.csv')
    covid.to_csv(cleaned_file_path, index=False)

    return cleaned_file_path

if __name__ == "__main__":
    fetch_and_clean_data()
