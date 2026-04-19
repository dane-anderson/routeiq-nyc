import requests
import os
from dotenv import load_dotenv
from google.transit import gtfs_realtime_pb2

load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

MTA_FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs"

URL = "https://routes.googleapis.com/directions/v2:computeRoutes"



HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": "routes.duration,routes.legs.steps,routes.legs.steps.travelMode,routes.legs.steps.staticDuration,routes.legs.steps.transitDetails"
}

def get_mta_status():
    try:
        response = requests.get(MTA_FEED_URL, timeout=10)

        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)

        delay_count = 0

        for entity in feed.entity:
            if entity.HasField("trip_update"):
                for update in entity.trip_update.stop_time_update:
                    if update.HasField("arrival") and update.arrival.delay > 60:
                        delay_count += 1

        if delay_count > 50:
            return "Severe delays"
        elif delay_count > 10:
            return "Minor delays"
        else:
            return "On time"

    except Exception:
        return "MTA unavailable"

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

    best_route = min(
    result["routes"],
    key=lambda r: int(r["duration"].replace("s", ""))
    )

    steps = best_route["legs"][0]["steps"]
    walk_seconds = 0
    transit_steps = 0

    for step in steps:
        mode = step.get("travelMode")
        
    if mode == "WALK":
        walk_seconds += int(step["staticDuration"].replace("s", ""))
    elif mode == "TRANSIT":
        ride_seconds += int(step["staticDuration"].replace("s", ""))
        transit_steps += 1

    ride_seconds = seconds - walk_seconds
    delay_status = get_mta_status()

   
    return {
        "eta_seconds": seconds,
        "walk_minutes": round(walk_seconds / 60),
        "ride_minutes": round(ride_seconds / 60),
        "transfers": max(transit_steps - 1, 0),
        "delay_status": delay_status,
        "best_route": best_route
    }

if __name__ == "__main__":
    origin = {"latitude": 40.7580, "longitude": -73.9855}
    destination = {"latitude": 40.7128, "longitude": -74.0060}

    drive = get_drive_eta(origin, destination)
    transit = get_transit_eta(origin, destination)

    print("Drive:", drive)
    print("Transit:", transit)

def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        code = data["current_weather"]["weathercode"]

       
        if code in [0]:
            return "clear"
        elif code in [1, 2, 3]:
            return "cloudy"
        elif code in [51, 53, 55, 61, 63, 65]:
            return "rain"
        elif code in [71, 73, 75]:
            return "snow"
        else:
            return "clear"

    except:
        return "clear"