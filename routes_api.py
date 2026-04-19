import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

MTA_FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs"
URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": (
        "routes.duration,"
        "routes.legs.steps,"
        "routes.legs.steps.travelMode,"
        "routes.legs.steps.staticDuration,"
        "routes.legs.steps.transitDetails"
    ),
}


def get_mta_status() -> str:
    return "MTA unavailable"


def geocode_address(address: str) -> dict | None:
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": API_KEY,
    }

    response = requests.get(url, params=params, timeout=10)
    result = response.json()

    if result.get("status") != "OK" or not result.get("results"):
        return None

    location = result["results"][0]["geometry"]["location"]

    return {
        "latitude": location["lat"],
        "longitude": location["lng"],
    }


def get_drive_eta(origin: dict, destination: dict) -> int:
    data = {
        "origin": {"location": {"latLng": origin}},
        "destination": {"location": {"latLng": destination}},
        "travelMode": "DRIVE",
    }

    response = requests.post(URL, headers=HEADERS, json=data, timeout=15)
    result = response.json()

    if "routes" not in result or not result["routes"]:
        return 9999

    return int(result["routes"][0]["duration"].replace("s", ""))


def _route_score(route: dict) -> int:
    steps = route["legs"][0]["steps"]
    total_seconds = int(route["duration"].replace("s", ""))

    walk_seconds = 0
    transit_steps = 0
    has_bus = False

    for step in steps:
        mode = step.get("travelMode")

        if mode == "WALK":
            walk_seconds += int(step["staticDuration"].replace("s", ""))

        elif mode == "TRANSIT":
            transit_steps += 1
            details = step.get("transitDetails", {})
            vehicle_type = details.get("transitLine", {}).get("vehicle", {}).get("type", "")

            if vehicle_type == "BUS":
                has_bus = True

    transfers = max(transit_steps - 1, 0)
    score = total_seconds + (walk_seconds * 2) + (transfers * 300)

    if has_bus:
        score += 100000

    return score


def get_transit_eta(origin: dict, destination: dict) -> dict | int:
    data = {
        "origin": {"location": {"latLng": origin}},
        "destination": {"location": {"latLng": destination}},
        "travelMode": "TRANSIT",
        "departureTime": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "computeAlternativeRoutes": True,
    }

    response = requests.post(URL, headers=HEADERS, json=data, timeout=15)
    result = response.json()

    if "routes" not in result or not result["routes"]:
        return 9999

    best_route = min(result["routes"], key=_route_score)
    seconds = int(best_route["duration"].replace("s", ""))

    steps = best_route["legs"][0]["steps"]
    walk_seconds = 0
    transit_steps = 0
    ride_seconds = 0

    line = ""
    departure = ""
    arrival = ""
    transit_legs = []

    for step in steps:
        mode = step.get("travelMode")

        if mode == "WALK":
            walk_seconds += int(step["staticDuration"].replace("s", ""))

        elif mode == "TRANSIT":
            details = step.get("transitDetails", {})
            transit_line = details.get("transitLine", {})
            stop_details = details.get("stopDetails", {})

            vehicle_type = transit_line.get("vehicle", {}).get("type", "")
            vehicle_name = transit_line.get("vehicle", {}).get("name", {}).get("text", "")
            name_short = transit_line.get("nameShort", [])

            if vehicle_type == "SUBWAY":
                if name_short and isinstance(name_short, list):
                    current_line = "/".join(name_short)
                else:
                    current_line = transit_line.get("shortName") or transit_line.get("name", "")
            else:
                current_line = vehicle_name or transit_line.get("shortName") or transit_line.get("name", "")

            current_departure = stop_details.get("departureStop", {}).get("name", "")
            current_arrival = stop_details.get("arrivalStop", {}).get("name", "")

            transit_legs.append({
                "line": current_line,
                "departure": current_departure,
                "arrival": current_arrival,
                "vehicle_type": vehicle_type,
            })

            if not departure:
                departure = current_departure
            arrival = current_arrival
            line = current_line

            ride_seconds += int(step["staticDuration"].replace("s", ""))
            transit_steps += 1

    if ride_seconds == 0:
        ride_seconds = max(seconds - walk_seconds, 0)

    delay_status = get_mta_status()

    return {
        "eta_seconds": seconds,
        "walk_minutes": round(walk_seconds / 60),
        "ride_minutes": round(ride_seconds / 60),
        "transfers": max(transit_steps - 1, 0),
        "delay_status": delay_status,
        "best_route": best_route,
        "line": line,
        "departure": departure,
        "arrival": arrival,
        "transit_legs": transit_legs,
    }


def get_weather(lat: float, lon: float) -> str:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
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

    except Exception:
        return "clear"


if __name__ == "__main__":
    origin = {"latitude": 40.7580, "longitude": -73.9855}
    destination = {"latitude": 40.7128, "longitude": -74.0060}

    drive = get_drive_eta(origin, destination)
    transit = get_transit_eta(origin, destination)

    print("Drive:", drive)
    print("Transit:", transit)