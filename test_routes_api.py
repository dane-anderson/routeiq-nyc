import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

url = "https://routes.googleapis.com/directions/v2:computeRoutes"

headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": "routes.duration,routes.distanceMeters"
}

data = {
    "origin": {
        "location": {
            "latLng": {
                "latitude": 40.7580,
                "longitude": -73.9855
            }
        }
    },
    "destination": {
        "location": {
            "latLng": {
                "latitude": 40.7128,
                "longitude": -74.0060
            }
        }
    },
    "travelMode": "TRANSIT",
    "transitPreferences": {
        "routingPreference": "LESS_WALKING"
    }
}

response = requests.post(url, headers=headers, json=data)

print(response.json())
