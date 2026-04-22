import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
import xml.etree.ElementTree as ET

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

MTA_FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs"
URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": (
        "routes.duration,"
        "routes.polyline.encodedPolyline,"
        "routes.legs.steps,"
        "routes.legs.steps.travelMode,"
        "routes.legs.steps.staticDuration,"
        "routes.legs.steps.transitDetails"
    ),
}


def _normalize_line_symbols(line_symbol: str) -> list[str]:
    raw = (line_symbol or "").strip().upper()
    if not raw:
        return []

    pieces = [part.strip() for part in raw.replace(",", "/").split("/")]
    return [part for part in pieces if part]



def _map_mta_status(status_text: str, detail_text: str = "") -> str:
    status = (status_text or "").strip().upper()
    details = (detail_text or "").strip().upper()
    combined = f"{status} {details}".strip()

    severe_keywords = [
        "DELAYS",
        "SUSPENDED",
        "NO SERVICE",
        "PART SUSPENDED",
        "SIGNAL PROBLEMS",
        "SERVICE SUSPENDED",
    ]
    minor_keywords = [
        "PLANNED WORK",
        "SERVICE CHANGE",
        "SLOW",
        "REDUCED SERVICE",
    ]

    if any(keyword in combined for keyword in severe_keywords):
        return "Severe delays"
    if any(keyword in combined for keyword in minor_keywords):
        return "Minor delays"
    return "On time"



def get_mta_status(line_symbol: str = "") -> str:
    try:
        line_symbols = _normalize_line_symbols(line_symbol)
        url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2FserviceStatus"

        response = requests.get(url, timeout=8)
        if response.status_code != 200:
            return "On time"

        root = ET.fromstring(response.text)

        # If we know the subway line(s), try to match the exact line status first.
        if line_symbols:
            for line_node in root.findall(".//subway/line"):
                name_text = (line_node.findtext("name") or "").strip().upper()
                status_text = (line_node.findtext("status") or "").strip()
                text_node = line_node.find("text")
                detail_text = " ".join(text_node.itertext()).strip() if text_node is not None else ""

                if name_text in line_symbols:
                    return _map_mta_status(status_text, detail_text)

        # Fallback: infer a broad system status from all subway lines.
        system_statuses: list[str] = []
        for line_node in root.findall(".//subway/line"):
            status_text = (line_node.findtext("status") or "").strip()
            text_node = line_node.find("text")
            detail_text = " ".join(text_node.itertext()).strip() if text_node is not None else ""
            system_statuses.append(_map_mta_status(status_text, detail_text))

        if "Severe delays" in system_statuses:
            return "Severe delays"
        if "Minor delays" in system_statuses:
            return "Minor delays"
        return "On time"

    except Exception:
        return "On time"


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
    "origin": {
        "location": {
            "latLng": {
                "latitude": origin["latitude"],
                "longitude": origin["longitude"],
            }
        }
    },
    "destination": {
        "location": {
            "latLng": {
                "latitude": destination["latitude"],
                "longitude": destination["longitude"],
            }
        }
    },
    "travelMode": "DRIVE",
}

    response = requests.post(URL, headers=HEADERS, json=data, timeout=15)
    result = response.json()

    if "routes" not in result or not result["routes"]:
        return 9999

    route = result["routes"][0]

    duration = route["duration"]
    polyline = route["polyline"]["encodedPolyline"]

    return {
    "eta_seconds": int(duration.replace("s", "")),
    "polyline": polyline
    }


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
        "origin": {
            "location": {
                "latLng": {
                    "latitude": origin["latitude"],
                    "longitude": origin["longitude"],
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": destination["latitude"],
                    "longitude": destination["longitude"],
                }
            }
        },
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
    route_steps = []

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

    if transit_legs:
        first_departure = transit_legs[0]["departure"]

        route_steps = [
            {
                "type": "walk",
                "text": f"👣 Walk {round(walk_seconds / 60)} min to {first_departure}"
            }
        ]

        for i, leg in enumerate(transit_legs):
            route_steps.append({
                "type": "train",
                "text": f"🚇 Take {leg['line']} from {leg['departure']} to {leg['arrival']}"
            })

            if i < len(transit_legs) - 1:
                next_leg = transit_legs[i + 1]
                route_steps.append({
                    "type": "transfer",
                    "text": f"🔁 Transfer at {leg['arrival']} to {next_leg['line']}"
                })

        route_steps.append({
            "type": "walk",
            "text": f"👣 Walk to {destination.get('label', 'destination')}"
        })
    else:
        route_steps = [
            {
                "type": "walk",
                "text": f"👣 Walk {round(walk_seconds / 60)} min"
            }
        ]

    if ride_seconds == 0:
        ride_seconds = max(seconds - walk_seconds, 0)

    delay_status = get_mta_status(line)

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
        "route_steps": route_steps,
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