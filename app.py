from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
import requests
import datetime
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # For flashing messages


# URL-encode your username and password
username = quote_plus("shreyasmagdum")
password = quote_plus("Shreyas@123")  # Encodes the '@' character

# Connection string with encoded credentials
connection_string = f"mongodb+srv://{username}:{password}@shreyas.e7byf.mongodb.net/"

# Initialize MongoClient
client = MongoClient(connection_string)

# Specify the database and collection
db = client['weather_app']
weather_collection = db['weather_data']

# OpenWeatherMap API configuration
API_KEY = os.getenv("WEATHER_API_KEY", "c9c4f75aed9854bf409844e059bf0f37")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@app.route('/get_weather', methods=['POST'])
def get_weather():
    """Fetch weather data for the entered city."""
    city = request.form.get('city')
    if not city:
        flash("City name cannot be empty.", "danger")
        return redirect(url_for('index'))

    # Fetch weather data from the API
    params = {'q': city, 'appid': API_KEY, 'units': 'metric'}
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        weather_data = {
            'city': city.title(),
            'temperature': data['main']['temp'],
            'description': data['weather'][0]['description'].capitalize(),
            'icon': data['weather'][0]['icon'],
            'date': datetime.datetime.now()
        }

        # Store the data in MongoDB
        weather_collection.insert_one(weather_data)

        return render_template('weather.html', weather=weather_data)
    elif response.status_code == 404:
        flash("City not found. Please try again.", "danger")
        return redirect(url_for('index'))
    else:
        flash("Unable to fetch weather data. Please try again later.", "danger")
        return redirect(url_for('index'))

@app.route('/history')
def history():
    """Fetch and display weather search history."""
    # Pagination setup
    page = int(request.args.get('page', 1))
    per_page = 5
    skip = (page - 1) * per_page
    total_records = weather_collection.count_documents({})
    total_pages = (total_records + per_page - 1) // per_page

    records = weather_collection.find().sort('date', -1).skip(skip).limit(per_page)
    return render_template(
        'history.html',
        records=records,
        page=page,
        total_pages=total_pages
    )

if __name__ == '__main__':
    app.run(debug=True)
