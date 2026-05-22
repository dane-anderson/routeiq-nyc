import os
from datetime import datetime, timezone
from datetime import timedelta
import requests
from dotenv import load_dotenv
import xml.etree.ElementTree as ET

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
PLACES_API_KEY = os.getenv("PLACES_API_KEY")

MTA_FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs"
URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": (
        "routes.duration,"
        "routes.polyline.encodedPolyline,"
        "routes.legs.steps,"
        "routes.legs.steps.polyline.encodedPolyline,"
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
    
def get_mta_status_detail(line_symbol: str = "") -> dict:
    status = get_mta_status(line_symbol)

    if status == "Severe delays":
        return {
            "status": "Severe delays",
            "detail": "Major service disruption reported",
            "delay_minutes": 8,
        }

    if status == "Minor delays":
        return {
            "status": "Minor delays",
            "detail": "Service changes or delays reported",
            "delay_minutes": 4,
        }

    if status == "Unavailable":
        return {
            "status": "Unavailable",
            "detail": "Live status unavailable",
            "delay_minutes": 0,
        }

    return {
        "status": "On time",
        "detail": "No active delays reported",
        "delay_minutes": 0,
    }

NYC_BOUNDS = {
    "north": 40.9176,
    "south": 40.4774,
    "east": -73.7004,
    "west": -74.2591,
}


def is_in_nyc(lat: float, lng: float) -> bool:
    return (
        NYC_BOUNDS["south"] <= lat <= NYC_BOUNDS["north"]
        and NYC_BOUNDS["west"] <= lng <= NYC_BOUNDS["east"]
    )


def geocode_address(address: str) -> dict | None:
    url = "https://maps.googleapis.com/maps/api/geocode/json"

    params = {
        "address": f"{address}, New York, NY",
        "key": API_KEY,
        "bounds": "40.4774,-74.2591|40.9176,-73.7004",
        "region": "us",
        "components": "country:US|administrative_area:NY",
    }

    response = requests.get(url, params=params, timeout=10)
    result = response.json()

   

    if result.get("status") != "OK" or not result.get("results"):
        return None

    location = result["results"][0]["geometry"]["location"]
    lat = location["lat"]
    lng = location["lng"]

    if not is_in_nyc(lat, lng):
        return None

    return {
        "latitude": lat,
        "longitude": lng,
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

    print("DRIVE DEBUG:", result)

    if "routes" not in result or not result["routes"]:
        return None

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


def get_transit_eta(origin: dict, destination: dict, departure_time=None) -> dict | int:
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
        "departureTime": (departure_time or datetime.now(timezone.utc)).replace(microsecond=0).isoformat(),
        "computeAlternativeRoutes": True,
    }

    response = requests.post(URL, headers=HEADERS, json=data, timeout=15)
    result = response.json()

    if "routes" not in result or not result["routes"]:
        return None

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

            departure_time = stop_details.get("departureTime", "")
            arrival_time = stop_details.get("arrivalTime", "")

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
            step_polyline = step.get("polyline", {}).get("encodedPolyline", "")


            transit_legs.append({
                "line": current_line,
                "departure": current_departure,
                "arrival": current_arrival,
                "vehicle_type": vehicle_type,
                "polyline": step_polyline,
                "departure_time": departure_time,
                "arrival_time": arrival_time,
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
                "text": f"👣 Walk {round((walk_seconds / 60) * 0.72)} min to {first_departure}"
            }
        ]

        for i, leg in enumerate(transit_legs):
            board_time = ""

            if leg.get("departure_time"):
                try:
                    departure_dt = datetime.fromisoformat(
                        leg["departure_time"].replace("Z", "+00:00")
                    ).astimezone()

                    board_time = (
                        departure_dt
                        .strftime("%I:%M %p")
                        .lstrip("0")
                    )

                    minutes_until = round(
                        (departure_dt - datetime.now().astimezone()).total_seconds() / 60
                    )

                    if minutes_until > 0:
                        countdown_text = f" • Boards in {minutes_until} min"
                    else:
                        countdown_text = ""

                except:
                    board_time = ""
                    countdown_text = ""

            else:
                countdown_text = ""

            train_text = (
                f"🚇 Board {leg['line']} at {board_time}{countdown_text}\n"
                f"{leg['departure']} → {leg['arrival']}"
                if board_time
                else
                f"🚇 Take {leg['line']} from {leg['departure']} to {leg['arrival']}"
            )

            route_steps.append({
                "type": "train",
                "text": train_text
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

    adjusted_walk_seconds = int(walk_seconds * 0.72)
    seconds = int((seconds - walk_seconds) + adjusted_walk_seconds) 

    mta_status = get_mta_status_detail(line)

    return {
        "eta_seconds": seconds,
        "walk_minutes": round((walk_seconds / 60) * 0.72),
        "ride_minutes": round(ride_seconds / 60),
        "transfers": max(transit_steps - 1, 0),
        "delay_status": mta_status["status"],
        "delay_detail": mta_status["detail"],
        "delay_minutes": mta_status["delay_minutes"],
        "best_route": best_route,
        "line": line,
        "departure": departure,
        "arrival": arrival,
        "transit_legs": transit_legs,
        "route_steps": route_steps,
    }

def get_weather_at_arrival(lat: float, lon: float, eta_minutes: int) -> dict:
    arrival_time = datetime.now() + timedelta(minutes=eta_minutes)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,apparent_temperature,precipitation,rain,snowfall,cloud_cover,weather_code",
        "temperature_unit": "fahrenheit",
        "timezone": "America/New_York",
        "forecast_days": 1,
    }

    try:
        response = requests.get(url, params=params, timeout=8)
        data = response.json()
        hourly = data["hourly"]

        times = hourly["time"]

        closest_index = min(
            range(len(times)),
            key=lambda i: abs(datetime.fromisoformat(times[i]) - arrival_time)
        )

        temp = round(hourly["temperature_2m"][closest_index])
        feels_like = round(hourly["apparent_temperature"][closest_index])
        rain = hourly["rain"][closest_index]
        snow = hourly["snowfall"][closest_index]
        cloud_cover = hourly["cloud_cover"][closest_index]

        if snow >= 0.25:
            condition = "Heavy snow"
            detail = "Heavy snowfall expected at arrival"
            icon = "❄️"
        elif snow > 0.05:
            condition = "Snow"
            detail = "Snow expected at arrival"
            icon = "❄️"
        elif snow > 0:
            condition = "Light snow"
            detail = "Light snowfall possible"
            icon = "🌨️"
        elif rain >= 0.35:
            condition = "Heavy rain"
            detail = "Heavy rain expected at arrival"
            icon = "⛈️"
        elif rain >= 0.12:
            condition = "Rain"
            detail = "Rain likely at arrival"
            icon = "🌧️"
        elif rain > 0:
            condition = "Sprinkling"
            detail = "Light drizzle expected at arrival"
            icon = "🌦️"
        elif cloud_cover >= 80:
            condition = "Cloudy skies"
            detail = "Overcast skies at arrival"
            icon = "☁️"
        elif cloud_cover >= 45:
            condition = "Partly cloudy"
            detail = "Some clouds expected at arrival"
            icon = "⛅"
        else:
            condition = "Clear skies"
            detail = "Clear conditions expected at arrival"
            icon = "☀️"

        return {
            "icon": icon,
            "condition": condition,
            "detail": detail,
            "temp": temp,
            "feels_like": feels_like,
            "arrival_time": arrival_time.strftime("%I:%M %p").lstrip("0"),
        }

    except Exception:
        return {
            "icon": "🌤️",
            "condition": "Weather unavailable",
            "detail": "Couldn’t load arrival weather",
            "temp": "—",
            "feels_like": "—",
            "arrival_time": arrival_time.strftime("%I:%M %p").lstrip("0"),
        }

def get_nearby_coffee(destination: dict) -> dict | None:
    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": PLACES_API_KEY,
        "X-Goog-FieldMask": (
            "places.displayName,"
            "places.rating,"
            "places.userRatingCount,"
            "places.googleMapsUri"
        ),
    }

    payload = {
        "textQuery": "coffee shop near destination",
        "maxResultCount": 8,
        "locationBias": {
            "circle": {
                "center": {
                    "latitude": destination["latitude"],
                    "longitude": destination["longitude"],
                },
                "radius": 350,
            }
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = response.json()

        coffee_spots = []

        for place in data.get("places", []):
            rating = place.get("rating", 0)
            reviews = place.get("userRatingCount", 0)

            if rating and reviews >= 25:
                coffee_spots.append({
                    "name": place.get("displayName", {}).get("text", "Coffee shop"),
                    "rating": rating,
                    "reviews": reviews,
                    "url": place.get("googleMapsUri", "#"),
                })

        if not coffee_spots:
            return None

        return sorted(
            coffee_spots,
            key=lambda spot: (spot["rating"], spot["reviews"]),
            reverse=True
        )[0]

    except Exception as e:
        print("COFFEE API ERROR:", e)
        return None

def get_best_nearby_bagel(destination: dict) -> dict | None:
    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": PLACES_API_KEY,
        "X-Goog-FieldMask": (
            "places.displayName,"
            "places.rating,"
            "places.userRatingCount,"
            "places.googleMapsUri"
        ),
    }

    payload = {
        "textQuery": "bagel shop near destination",
        "maxResultCount": 8,
        "locationBias": {
            "circle": {
                "center": {
                    "latitude": destination["latitude"],
                    "longitude": destination["longitude"],
                },
                "radius": 350,
            }
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = response.json()

        bagel_spots = []

        for place in data.get("places", []):
            rating = place.get("rating", 0)
            reviews = place.get("userRatingCount", 0)

            if rating and reviews:
                bagel_spots.append({
                    "name": place.get("displayName", {}).get("text", "Bagel shop"),
                    "rating": rating,
                    "reviews": reviews,
                    "url": place.get("googleMapsUri", "#"),
                })

        if not bagel_spots:
            return None

        return sorted(
            bagel_spots,
            key=lambda spot: (spot["rating"], spot["reviews"]),
            reverse=True
        )[0]

    except Exception as e:
        print("BAGEL API ERROR:", e)
        return None
    
def get_best_nearby_bodega(destination: dict) -> dict | None:
    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": PLACES_API_KEY,
        "X-Goog-FieldMask": (
            "places.displayName,"
            "places.rating,"
            "places.userRatingCount,"
            "places.googleMapsUri"
        ),
    }

    payload = {
        "textQuery": "deli grocery convenience store bodega",
        "maxResultCount": 8,
        "locationBias": {
            "circle": {
                "center": {
                    "latitude": destination["latitude"],
                    "longitude": destination["longitude"],
                },
                "radius": 350,
            }
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = response.json()

        bodega_spots = []

        for place in data.get("places", []):
            rating = place.get("rating", 0)
            reviews = place.get("userRatingCount", 0)

            bodega_spots.append({
                "name": place.get("displayName", {}).get("text", "Bodega"),
                "rating": rating,
                "reviews": reviews,
                "url": place.get("googleMapsUri", "#"),
            })

        if not bodega_spots:
            return None

        return bodega_spots[0]

    except Exception as e:
        print("BODEGA API ERROR:", e)
        return None