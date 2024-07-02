# import os
import pandas as pd
# import requests
# from io import StringIO
import plotly.graph_objects as go
import plotly.express as px
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import subprocess

# Call the data fetching and cleaning script
subprocess.run(["python", "fetch_and_clean_data.py"])

# Load the cleaned data
data = pd.read_csv('data/owid-covid-data-cleaned.csv')
countries = list(data["location"].unique())

# Initial selection of countries
selected_countries = ['Australia']
selected_policies = ['']
metric_options = ['excess_mortality', 'new_cases_smoothed', 'new_deaths_smoothed']

# Restriction policies to choose from
restriction_policies = ['residential', 'testing_policy', 'contact_tracing', 'containment_index', 'vaccination_policy',
                        'facial_coverings', 'restrictions_internal_movements', 'international_travel_controls',
                        'cancel_public_events', 'restriction_gatherings', 'close_public_transport', 'school_closures',
                        'stay_home_requirements', 'workplace_closures']

# Tooltip text for the average policy index
average_policy_index_tooltip_text = """
Composite measure on a scale of 0-100 of thirteen of the response metrics

"""

# Dash app initialization
app = dash.Dash(__name__)
# Define layout
########### CSS and div layout section ####################
# Add a function to generate the tooltip content
def generate_tooltip(content_id, tooltip_text):
    return html.Span([
        html.Span("ⓘ", id=content_id, style={"cursor": "pointer", "color": "blue", "fontSize": "18px"}),
        dbc.Tooltip(tooltip_text, target=content_id, placement="bottom", style={"backgroundColor": "white", "color": "black", "padding": "10px", "borderRadius": "5px", "boxShadow": "0px 0px 10px rgba(0, 0, 0, 0.1)"})
    ])

# In the layout, add the tooltips next to the relevant elements
app.layout = html.Div(className='dashboard-container', children=[
    html.H1(children='✨HI(R)US', className='h1 text-center pb-2'),

    # Top Tally Layout
    html.Div(className='tally-container', children=[
        html.Div(className='card-container', children=[
            html.Div(id='total-excess-mortality', className='card tally boxed'),
            html.H5('Total Excess Mortality', className='text-center'),
            generate_tooltip('total-excess-mortality-tooltip', 'This represents the total percentage of mortality surpassing the countries expected deaths...')
        ]),
        html.Div(className='card-container', children=[
            html.Div(id='total-new-cases', className='card tally boxed'),
            html.H5('Total Cases', className='text-center'),
            generate_tooltip('total-new-cases-tooltip', 'This represents the total number of COVID-19 cases for all selected countries...')
        ]),
        html.Div(className='card-container', children=[
            html.Div(id='total-new-deaths', className='card tally boxed'),
            html.H5('Total Deaths', className='text-center'),
            generate_tooltip('total-new-deaths-tooltip', 'This represents the total number of COVID-19 deaths for all selected countries...')
        ]),
        html.Div(className='card-container', children=[
            html.Div(id='average-policy-index', className='card tally boxed'),
            html.H5('Average Policy Index', className='text-center'),
           generate_tooltip('average-policy-index-tooltip', average_policy_index_tooltip_text)
        
        ]),
    ]),

    ###### Filters ######
    html.Div(className='filters-graphs-container', children=[
        # Filter containers (side by side)
        html.Div(className='filters-container', children=[
            html.Div(className='filter-container', children=[
                dcc.Dropdown(
                    id='country-dropdown',
                    options=[{'label': country, 'value': country} for country in countries],
                    value=selected_countries,
                    multi=True,
                    className='fullwidth'
                ),
                generate_tooltip('country-dropdown-tooltip', 'Select countries to include in the analysis...')
            ]),
            html.Div(className='filter-container', children=[
                dcc.Dropdown(
                    id='policy-dropdown',
                    options=[{'label': policy, 'value': policy} for policy in restriction_policies],
                    value=selected_policies,
                    multi=True,
                    className='fullwidth'
                ),
                generate_tooltip('policy-dropdown-tooltip', 'Select policies to include in the analysis...')
            ]),
            html.Div(className='filter-container', children=[
                dcc.Dropdown(
                    id='metric-dropdown',
                    options=[{'label': metric.replace('_', ' ').title(), 'value': metric} for metric in metric_options],
                    value='excess_mortality',
                    className='fullwidth'
                ),
                generate_tooltip('metric-dropdown-tooltip', 'Select the metric to display in the graphs...')
            ]),
        ]),
        #### Graph placements ####
        # Line graph for the selected metric over time (full width)
        # Heatmap for policy correlations
        html.Div(className='maps-container', children=[
            html.Div(className='map-container', children=[
                dcc.Graph(
                    id='heatmap',
                    figure={}
                ),
            ]),

        # Maps section (split into two)
            # Choropleth map for the selected metric by country
            html.Div(className='map-container', children=[
                dcc.Graph(
                    id='excess-mortality-map',
                    figure={}
                ),
            ]),
            
        ]),
        html.Div(className='graph-container', children=[
            dcc.Graph(
                id='excess-mortality-graph',
                figure={}
            ),
        ]),
    ]),
])
########### Plot section ####################
###Line graph###
# Define callback to update the total excess mortality text and line graph
@app.callback(
    Output('excess-mortality-graph', 'figure'),
    [Input('country-dropdown', 'value'),
     Input('policy-dropdown', 'value'),
     Input('metric-dropdown', 'value')]
)
def update_excess_mortality_graph(selected_countries, selected_policies, selected_metric):
    filtered_data = data[data["location"].isin(selected_countries)]

    # Create line graph for the selected metric over time
    excess_mortality_fig = go.Figure()

    # Add trace for selected metric (mortality, cases, or deaths)
    for country in selected_countries:
        country_data = filtered_data[filtered_data['location'] == country]
        
        if selected_metric == 'new_cases':
            y_data = country_data['new_cases_smoothed']  
        elif selected_metric == 'new_deaths':
            y_data = country_data['new_deaths_smoothed'] 
        else:
            y_data = country_data[selected_metric] 
        excess_mortality_fig.add_trace(go.Scatter(
            x=country_data['date'],
            y=y_data,
            mode='lines',
            name=country,
            yaxis='y'  
        ))

    # Add traces for policy metrics
    for policy in selected_policies:
        for country in selected_countries:
            country_data = filtered_data[filtered_data['location'] == country]
            # Dynamically adjust to policy scale
            if policy != 'containment_index':
                y_data = country_data[policy]  
                y_axis = 'y2'  
            else:
                y_data = country_data[policy]  
                y_axis = 'y'  

            excess_mortality_fig.add_trace(go.Scatter(
                x=country_data['date'],
                y=y_data,
                mode='lines',
                name=f"{country} - {policy}",
                line=dict(dash='dot'),
                yaxis=y_axis  
            ))

    excess_mortality_fig.update_layout(
        xaxis_title='Date',
        yaxis_title=selected_metric.replace('_', ' ').title(),
        title=f'{selected_metric.replace("_", " ").title()} Over Time with Restriction Policies',
        yaxis=dict(
            title='Metric Value',  
            side='left',
            range=[0, filtered_data[selected_metric].max() * 1.1]  
        ),
        yaxis2=dict(
            title='Policy Level', 
            overlaying='y',
            side='right',
            range=[0, 5],  
            showgrid=False 
        ),      
    )

    return excess_mortality_fig


#### Tallies plus callbacks ####

@app.callback(
    Output('total-excess-mortality', 'children'),
    [Input('country-dropdown', 'value')]
)
def update_total_excess_mortality(selected_countries):
    filtered_data = data[data["location"].isin(selected_countries)]
    total_excess_mortality = filtered_data['excess_mortality'].mean()  # Use the appropriate column for excess mortality

    return html.Div([
        html.H4(f'{total_excess_mortality:,.2f}')
    ])


## Cases ##
@app.callback(
    Output('total-new-cases', 'children'),
    [Input('country-dropdown', 'value')]
)
def update_total_new_cases(selected_countries):
    filtered_data = data[data["location"].isin(selected_countries)]
    total_new_cases = filtered_data['new_cases'].sum()

    return html.Div([
        html.H4(f'{total_new_cases:,.2f}')
    ])


## Deaths ##
@app.callback(
    Output('total-new-deaths', 'children'),
    [Input('country-dropdown', 'value')]
)
def update_total_new_deaths(selected_countries):
    filtered_data = data[data["location"].isin(selected_countries)]
    total_new_deaths = filtered_data['new_deaths'].sum()

    return html.Div([
        html.H4(f'{total_new_deaths:,.2f}')
    ])

## Average policy index ##
@app.callback(
    Output('average-policy-index', 'children'),
    [Input('country-dropdown', 'value')]
)
def update_average_policy_index(selected_countries):
    filtered_data = data[data["location"].isin(selected_countries)]
    average_policy_index = filtered_data['containment_index'].mean()

    return html.Div([
        html.H4(f'{average_policy_index:,.2f}')
    ])

### Geomap/ Choropleth plot ### 
@app.callback(
    Output('excess-mortality-map', 'figure'),
    [Input('country-dropdown', 'value'),
     Input('metric-dropdown', 'value')]
)
def update_excess_mortality_map(selected_countries, selected_metric):
    filtered_data = data[data["location"].isin(selected_countries)]
    
    if selected_metric == 'excess_mortality':
        country_totals = (
            filtered_data.groupby('location')[selected_metric]
            .mean()  # Calculate mean excess mortality for each country
            .reset_index()
        )
    else:
        country_totals = (
            filtered_data.groupby('location')[selected_metric]
            .sum()  # Sum the selected metric for each country
            .reset_index()
        )
    
    fig = px.choropleth(
        country_totals,
        locations="location",
        locationmode='country names',
        color=selected_metric,
        hover_name="location",
        color_continuous_scale=px.colors.sequential.Plasma,
        labels={selected_metric: selected_metric.replace('_', ' ').title()},
        title=f'Total {selected_metric.replace("_", " ").title()} by Country'
    )

    fig.update_layout(
        geo=dict(
            showcoastlines=True,
            showland=True,
        )
    )

    return fig


### heatmap ###

@app.callback(
    Output('heatmap', 'figure'),
    [Input('country-dropdown', 'value'),
     Input('metric-dropdown', 'value')]
)
def update_heatmap(selected_countries, selected_metric):
    EXPLAN_VAR = restriction_policies

    # Filtering data and calculating correlation
    filtered_data = data[data["location"].isin(selected_countries)]
    corr_geo = filtered_data.groupby('location').apply(lambda x: x[EXPLAN_VAR].corrwith(x[selected_metric], method='spearman').round(2))

    # Drop rows where all explanatory variables are NaN
    corr_geo = corr_geo.dropna(how='all').reset_index()

    # Heatmap Plotly
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=corr_geo[EXPLAN_VAR].values.T,
        x=corr_geo['location'],
        y=EXPLAN_VAR,
        colorscale='balance',
        colorbar=dict(title='Spearman Correlation'),
    ))

    heatmap_fig.update_layout(
        title=f'Correlation between policies and {selected_metric.replace("_", " ").title()}, by country',
        xaxis_title='Countries',
        yaxis_title='COVID-19 public health policies'
    )

    return heatmap_fig

if __name__ == '__main__':
    app.run_server(debug=True)
