import os
from dotenv import load_dotenv


load_dotenv()


GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')


DEFAULT_LOCATION = {
    'lat': 25.2048,
    'lng': 55.2708
}


DEFAULT_RADIUS = 50000 