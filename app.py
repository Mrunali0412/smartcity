from flask import Flask, render_template
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

app = Flask(__name__)

def load_data(file_path):
    """Loads data from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        return None

def create_traffic_flow_chart(df):
    """Creates a bar chart of traffic flow at different locations."""
    traffic_data = df[df['sensor_type'] == 'traffic']
    fig = go.Figure(data=[go.Bar(x=traffic_data['location'], y=traffic_data['value'], text=traffic_data['value'], textposition='outside')])
    fig.update_layout(title='Traffic Flow at Intersections', xaxis_title='Intersection', yaxis_title='Vehicles/Hour')
    return json.dumps(fig.to_json())

def create_air_quality_chart(df):
    """Creates a scatter plot of air quality at different locations."""
    air_quality_data = df[df['sensor_type'] == 'air_quality']
    fig = go.Figure(data=[go.Scatter(x=air_quality_data['location'], y=air_quality_data['value'], mode='markers', text=air_quality_data['value'], hoverinfo='text+x')])
    fig.update_layout(title='Air Quality Levels', xaxis_title='Location', yaxis_title='Pollutant Level (µg/m³)')
    return json.dumps(fig.to_json())

def create_energy_consumption_chart(df):
    """Creates a pie chart of energy consumption by zone."""
    energy_data = df[df['sensor_type'] == 'energy']
    zone_consumption = energy_data.groupby('location')['value'].sum().reset_index()
    fig = go.Figure(data=[go.Pie(labels=zone_consumption['location'], values=zone_consumption['value'], hoverinfo='percent', textinfo='value')])
    fig.update_layout(title='Energy Consumption by Zone')
    return json.dumps(fig.to_json())

def create_transport_usage_chart(df):
    """Creates a line chart of public transport usage over time (simplified)."""
    transport_data = df[df['sensor_type'] == 'transport']
    # For a proper line chart, you'd likely need more temporal data
    fig = go.Figure(data=[go.Bar(x=transport_data['location'], y=transport_data['value'], text=transport_data['value'], textposition='outside')])
    fig.update_layout(title='Public Transport Usage', xaxis_title='Station', yaxis_title='Passengers')
    return json.dumps(fig.to_json())

@app.route('/')
def index():
    data = load_data('data/smart_city_data.csv')
    if data is None:
        return "Error: Could not load data."

    traffic_chart_json = create_traffic_flow_chart(data)
    air_quality_chart_json = create_air_quality_chart(data)
    energy_chart_json = create_energy_consumption_chart(data)
    transport_chart_json = create_transport_usage_chart(data)

    return render_template('index.html',
                           traffic_chart_json=traffic_chart_json,
                           air_quality_chart_json=air_quality_chart_json,
                           energy_chart_json=energy_chart_json,
                           transport_chart_json=transport_chart_json)

if __name__ == '__main__':
    app.run(debug=True)