from flask import Flask, request, render_template, redirect
from flask import jsonify
import psycopg2
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as make_subplots
import json
from psycopg2 import sql
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv

conn = psycopg2.connect(
    host="localhost",
    database="smartcity",
    user="postgres",
    password="postgresql"
)
cursor= conn.cursor()
load_dotenv()  # Load environment variables from .env file
app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') #  Use environment variable
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # To suppress a warning
db = SQLAlchemy(app)



class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    sensor_type = Column(String(50), nullable=False)
    location = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)

    def __repr__(self):
        return f"<SensorData(timestamp='{self.timestamp}', sensor_type='{self.sensor_type}', location='{self.location}', value={self.value}, unit='{self.unit}')>"
def create_database():
    """Creates the database and tables."""
    with app.app_context():
        db.create_all()
        # Check if the table is empty before adding initial data
        if not SensorData.query.first():
            insert_initial_data()

def insert_initial_data():
    """Inserts initial data into the database."""
    initial_data = [
        SensorData(timestamp='2025-04-17 00:00:00', sensor_type='traffic', location='Intersection A', value=150, unit='vehicles/hour'),
        SensorData(timestamp='2025-04-17 00:00:00', sensor_type='air_quality', location='Downtown', value=15, unit='µg/m³'),
        SensorData(timestamp='2025-04-17 00:00:00', sensor_type='energy', location='Residential Zone 1', value=220, unit='kWh'),
        SensorData(timestamp='2025-04-17 00:00:00', sensor_type='transport', location='Bus Station Central', value=75, unit='passengers'),
        SensorData(timestamp='2025-04-17 00:15:00', sensor_type='traffic', location='Intersection B', value=180, unit='vehicles/hour'),
        SensorData(timestamp='2025-04-17 00:15:00', sensor_type='air_quality', location='Industrial Area', value=45, unit='µg/m³'),
        SensorData(timestamp='2025-04-17 00:15:00', sensor_type='energy', location='Commercial Zone', value=350, unit='kWh'),
        SensorData(timestamp='2025-04-17 00:15:00', sensor_type='transport', location='Train Station Main', value=120, unit='passengers'),
    ]
    with app.app_context():
        db.session.add_all(initial_data)
        db.session.commit()



def create_traffic_flow_chart():
    """Creates a bar chart of traffic flow at different locations using data from the database."""
    with app.app_context():
        traffic_data = SensorData.query.filter_by(sensor_type='traffic').all()
        locations = [data.location for data in traffic_data]
        values = [data.value for data in traffic_data]

        fig = go.Figure(data=[go.Bar(x=locations, y=values, text=values, textposition='outside')])
        fig.update_layout(title='Traffic Flow at Intersections', xaxis_title='Intersection',
                          yaxis_title='Vehicles/Hour')
        return json.dumps(fig.to_json())
def create_air_quality_chart():
    """Creates a scatter plot of air quality at different locations using data from the database."""
    with app.app_context():
        air_quality_data = SensorData.query.filter_by(sensor_type='air_quality').all()
        locations = [data.location for data in air_quality_data]
        values = [data.value for data in air_quality_data]
        fig = go.Figure(data=[go.Scatter(x=locations, y=values, mode='markers', text=values, hoverinfo='text+x')])
        fig.update_layout(title='Air Quality Levels', xaxis_title='Location', yaxis_title='Pollutant Level (µg/m³)')
        return json.dumps(fig.to_json())
def create_energy_consumption_chart():
    """Creates a pie chart of energy consumption by zone using data from the database."""
    with app.app_context():
        energy_data = SensorData.query.filter_by(sensor_type='energy').all()
        # Use a dictionary to store and accumulate the sum of values for each location
        location_values = {}
        for data in energy_data:
            if data.location in location_values:
                location_values[data.location] += data.value
            else:
                location_values[data.location] = data.value

        locations = list(location_values.keys())
        values = list(location_values.values())
        fig = go.Figure(data=[go.Pie(labels=locations, values=values, hoverinfo='percent', textinfo='value')])
        fig.update_layout(title='Energy Consumption by Zone')
        return json.dumps(fig.to_json())

def create_transport_usage_chart():
    """Creates a bar chart of public transport usage using data from the database."""
    with app.app_context():
        transport_data = SensorData.query.filter_by(sensor_type='transport').all()
        locations = [data.location for data in transport_data]
        values = [data.value for data in transport_data]
        fig = go.Figure(data=[go.Bar(x=locations, y=values, text=values, textposition='outside')])
        fig.update_layout(title='Public Transport Usage', xaxis_title='Station', yaxis_title='Passengers')
        return json.dumps(fig.to_json())


@app.route('/')
def index():
    """Renders the main page with the charts."""
    traffic_chart_json = create_traffic_flow_chart()
    air_quality_chart_json = create_air_quality_chart()
    energy_chart_json = create_energy_consumption_chart()
    transport_chart_json = create_transport_usage_chart()
    return render_template('index.html',
                           traffic_chart_json=traffic_chart_json,
                           air_quality_chart_json=air_quality_chart_json,
                           energy_chart_json=energy_chart_json,
                           transport_chart_json=transport_chart_json)

@app.route('/data')  #  New route to expose data as JSON
def get_data():
    """Returns all sensor data as JSON."""
    with app.app_context():
        all_data = SensorData.query.all()
        data = [{'timestamp': item.timestamp,
                 'sensor_type': item.sensor_type,
                 'location': item.location,
                 'value': item.value,
                 'unit': item.unit} for item in all_data]
        return jsonify(data)
@app.route('/add-data')
def add_data():
    return render_template('sensor_data.html')

@app.route('/submit_sensor_data', methods=['POST'])
def submit_sensor_data():
    sensor_type = request.form['sensor_type']
    location = request.form['location']
    timestamp = request.form['timestamp']
    value = request.form['value']

    insert_query = sql.SQL("""
        INSERT INTO sensor_data (sensor_type, location, timestamp, value)
        VALUES (%s, %s, %s, %s)
    """)
    cursor.execute(insert_query, (sensor_type, location, timestamp, value))
    conn.commit()

    return "✅ Sensor data inserted successfully!"


if __name__ == '__main__':
    create_database()
    app.run(debug=True)