import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
print("API KEY LOADED:", API_KEY)

URL = "https://routes.googleapis.com/directions/v2:computeRoutes"



HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": "routes.duration"
}

def geocode_address(address):
    url = "https://maps.googleapis.com/maps/api/geocode/json"

    params = {
        "address": address,
        "key": API_KEY
    }

    response = requests.get(url, params=params)
    result = response.json()

    print("GEOCODE RESPONSE:", result)

    if result["status"] != "OK":
        return None

    location = result["results"][0]["geometry"]["location"]

    return {
        "latitude": location["lat"],
        "longitude": location["lng"]
    }

def get_drive_eta(origin, destination):
        data = {
            "origin": {"location": {"latLng": origin}},
            "destination": {"location": {"latLng": destination}},
            "travelMode": "DRIVE"
    }

        response = requests.post(URL, headers=HEADERS, json=data)
        result = response.json()
        print("DRIVE API RESPONSE:", result)

        if "routes" not in result:
            return 9999

        seconds = int(result["routes"][0]["duration"].replace("s", ""))
        return seconds  


def get_transit_eta(origin, destination):
    from datetime import datetime, timezone
    data = {
        "origin": {"location": {"latLng": origin}},
        "destination": {"location": {"latLng": destination}},
        "travelMode": "TRANSIT",
        "departureTime": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "computeAlternativeRoutes": True,
        "transitPreferences": {
            "routingPreference": "LESS_WALKING"
        }
    }

    response = requests.post(URL, headers=HEADERS, json=data)
    result = response.json()
    print("TRANSIT API RESPONSE:", result)

    if "routes" not in result:
        return 9999

    durations = [int(r["duration"].replace("s", "")) for r in result["routes"]]
    seconds = min(durations)
    return seconds

if __name__ == "__main__":
    origin = {"latitude": 40.7580, "longitude": -73.9855}
    destination = {"latitude": 40.7128, "longitude": -74.0060}

    drive = get_drive_eta(origin, destination)
    transit = get_transit_eta(origin, destination)

    print("Drive:", drive)
    print("Transit:", transit)