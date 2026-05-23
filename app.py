import streamlit as st
import requests

from streamlit_searchbox import st_searchbox
from datetime import datetime, timedelta, timezone

from decision_engine import make_decision
from ai_voice import generate_reasoning
from routes_api import (

    PLACES_API_KEY,
    get_drive_eta,
    get_transit_eta,
    geocode_address,
    get_nearby_coffee,
    get_best_nearby_bagel,
    get_best_nearby_bodega,
    get_weather_at_arrival

)
from utils.confidence import get_confidence_score
from components.cards import build_train_boxes_html
from components.hero import build_hero_card
import pandas as pd
import pydeck as pdk
import base64
from collections import defaultdict
from datetime import date


def search_nyc_places(searchterm: str):
    if not searchterm:
        return []

    url = "https://places.googleapis.com/v1/places:autocomplete"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": PLACES_API_KEY,
    }

    payload = {
        "input": searchterm,
        "includedRegionCodes": ["us"],
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                },
                "radius": 50000,
            }
        },
    }

    response = requests.post(url, headers=headers, json=payload, timeout=10)
    data = response.json()

    

    suggestions = data.get("suggestions", [])

    return [
        item["placePrediction"]["text"]["text"]
        for item in suggestions
        if "placePrediction" in item
    ][:5]

LINE_COLORS = {
    "1": "#EE352E", "2": "#EE352E", "3": "#EE352E",
    "4": "#00933C", "5": "#00933C", "6": "#00933C",
    "7": "#B933AD",
    "A": "#0039A6", "C": "#0039A6", "E": "#0039A6",
    "B": "#FF6319", "D": "#FF6319", "F": "#FF6319", "M": "#FF6319",
    "N": "#FCCC0A", "Q": "#FCCC0A", "R": "#FCCC0A", "W": "#FCCC0A",
    "J": "#996633", "Z": "#996633",
    "G": "#6CBE45",
    "L": "#A7A9AC",
}

IP_REQUEST_LOG = defaultdict(list)

MAX_REQUESTS_PER_IP_PER_DAY = 30


st.set_page_config(
    page_title="RouteIQ-NYC",
    page_icon="🚕",
    layout="wide"
)

if "route_requests" not in st.session_state:
    st.session_state.route_requests = 0

MAX_ROUTE_REQUESTS = 25


st.markdown("""
<style>
.block-container {
    max-width: 1400px;
    padding-top: 4rem;
    padding-right: 2.5rem;
    padding-left: 2.5rem;
    padding-bottom: 4rem;
}

html, body, [class*="css"] {
    background: #fafafa;
}

.app-header {
    background: #111111;
    color: #ffffff;
    border-radius: 22px;
    padding: 24px 28px;
    margin-bottom: 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.app-title {
    font-size: 32px;
    font-weight: 900;
    letter-spacing: -0.04em;
}

.app-subtitle {
    color: #d1d5db;
    margin-top: 5px;
    font-size: 14px;
    line-height: 1.45;
}

.update {
    display: inline-block;
    background: rgba(255,255,255,0.1);
    color: #f5f5f5;
    border-radius: 999px;
    padding: 8px 12px;
    font-size: 12px;
    font-weight: 700;
}

.card {
    background: #ffffff;
    border-radius: 20px;
    padding: 18px;
    border: 1px solid #ececec;
    margin-bottom: 14px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.035);
}

.why-card {
    background: #eaf1fb;
    border-radius: 20px;
    padding: 18px;
    border: 1px solid #d9e5f5;
    margin-bottom: 14px;
}

.hero {
    background: #FFC72C;
    border-radius: 24px;
    padding: 22px;
    margin-bottom: 14px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.08);
}

.hero-top {
    font-size: 12px;
    font-weight: 900;
    color: #FACC15;
}
.hero-main {
    font-size: 34px;
    font-weight: 900;
    line-height: 1.05;
    margin-top: 4px;
}

.hero-chip {
    background: rgba(255,255,255,0.55);
    color: #4d3a00;
    padding: 7px 12px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 800;
    display: inline-block;
    margin-top: 12px;
}

.leave-box {
    margin-top: 18px;
    background: rgba(17,17,17,0.9);
    color: white;
    border-radius: 18px;
    padding: 16px;
}

.leave-label {
    font-size: 12px;
    font-weight: 800;
    color: #FFC72C;
}

.leave-number {
    font-size: 42px;
    font-weight: 900;
    line-height: 1;
    margin-top: 4px;
}

.metric {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 0;
    font-size: 15px;
    border-bottom: 1px solid #f1f1f1;
}

.metric:last-child {
    border-bottom: none;
}

.section-title {
    font-weight: 900;
    font-size: 18px;
    margin-bottom: 10px;
}

.small-muted {
    font-size: 13px;
    color: #666;
    line-height: 1.5;
}

.stTextInput input {
    border-radius: 15px !important;
    padding: 0.85rem 1rem !important;
    font-size: 16px !important;
}

.stNumberInput input {
    border-radius: 15px !important;
}

.stSelectbox div[data-baseweb="select"] > div {
    border-radius: 15px !important;
}

.stButton > button {
    background: #FFC72C !important;
    color: #111111 !important;
    border: none !important;
    border-radius: 16px !important;
    padding: 0.9rem 1rem !important;
    font-size: 17px !important;
    font-weight: 900 !important;
    width: 100% !important;
    box-shadow: none !important;
}

.footer-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
}

.footer-item {
    background: #fafafa;
    border-radius: 14px;
    padding: 12px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)


def image_to_data_url(path: str) -> str:
    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
    return f"data:image/png;base64,{encoded}"


def hex_to_rgb(hex_color: str) -> list[int]:
    hex_color = hex_color.lstrip("#")
    return [int(hex_color[i:i + 2], 16) for i in (0, 2, 4)]


def get_line_badges_html(subway_data: dict) -> str:
    transit_legs = subway_data.get("transit_legs", [])
    symbols = []

    for leg in transit_legs:
        line_text = leg.get("line", "")
        if line_text:
            symbol = line_text.split("/")[0].split(" ")[0]
            if symbol and symbol not in symbols:
                symbols.append(symbol)

    if not symbols:
        line_text = subway_data.get("line", "")
        if line_text:
            symbols.append(line_text.split("/")[0].split(" ")[0])

    if not symbols:
        return ""

    badges_html = '<span style="display:inline-flex; align-items:center; gap:7px; margin-left:8px; flex-wrap:wrap;">'

    for symbol in symbols:
        color = LINE_COLORS.get(symbol, "#111111")
        text_color = "#111111" if color == "#FCCC0A" else "#FFFFFF"

        badges_html += (
            f'<span style="width:27px; height:27px; border-radius:50%; '
            f'display:inline-flex; align-items:center; justify-content:center; '
            f'color:{text_color}; font-size:14px; font-weight:900; '
            f'background:{color};">{symbol}</span>'
        )

    badges_html += '</span>'
    return badges_html


def decode_polyline(polyline_str: str) -> list[tuple[float, float]]:
    index, lat, lng, coordinates = 0, 0, 0, []

    while index < len(polyline_str):
        shift, result = 0, 0

        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break

        dlat = ~(result >> 1) if result & 1 else (result >> 1)
        lat += dlat

        shift, result = 0, 0

        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break

        dlng = ~(result >> 1) if result & 1 else (result >> 1)
        lng += dlng

        coordinates.append((lat / 1e5, lng / 1e5))

    return coordinates

def is_rate_limited(ip_address: str) -> bool:
    today = str(date.today())

    IP_REQUEST_LOG[ip_address] = [
        timestamp
        for timestamp in IP_REQUEST_LOG[ip_address]
        if timestamp == today
    ]

    return len(IP_REQUEST_LOG[ip_address]) >= MAX_REQUESTS_PER_IP_PER_DAY

def build_live_destination_html(destination_name, weather, subway_status, subway_detail, subway_delay_minutes, coffee_spots, bagel_spot, bodega_spot):
    coffee_html = ""
    if coffee_spots:
        spot = coffee_spots

        coffee_html = (
            f'<div style="padding:8px 0;">'
                f'<div style="font-weight:800;" '
                    f'<a href="{spot["url"]}" target="_blank" '
                    f'style="color:#111111; text-decoration:none;">'
                        f'{spot["name"]}'
                    f'</a>'
                f'</div>'
                f'<div style="font-size:13px; color:#666; margin-top:3px;">'
                    f'⭐ {spot["rating"]} • {spot["reviews"]} reviews'
                f'</div>'
                f'<div style="font-size:12px; color:#999; margin-top:4px;">'
                    f'Top rated coffee near destination'
                f'</div>'
            f'</div>'
        )
    else:
        coffee_html = (
            f'<div style="font-size:13px; color:#666;">'
                f'No nearby coffee spots found.'
            f'</div>'
        )

    bagel_html = ""

    if bagel_spot:
        spot = bagel_spot

        bagel_html = (
            f'<div style="padding:8px 0;">'
                f'<div style="font-weight:800;"'
                    f'<a href="{spot["url"]}" target="_blank" '
                    f'style="color:#111111; text-decoration:none;">'
                        f'{spot["name"]}'
                    f'</a>'
                f'</div>'
                f'<div style="font-size:13px; color:#666; margin-top:3px;">'
                    f'⭐ {spot["rating"]} • {spot["reviews"]} reviews'
                f'</div>'
                f'<div style="font-size:12px; color:#999; margin-top:4px;">'
                    f'Top rated bagel shop near destination'
                f'</div>'
            f'</div>'
        )
    else:
        bagel_html = (
            f'<div style="font-size:13px; color:#666;">'
                f'No nearby bagel shops found.'
            f'</div>'
        )

    bodega_html = ""

    if bodega_spot:
        spot = bodega_spot

        bodega_html = (
            f'<div style="padding:8px 0;">'
                f'<div style="font-weight:800;" '
                    f'<a href="{spot["url"]}" target="_blank" '
                    f'style="color:#111111; text-decoration:none;">'
                        f'{spot["name"]}'
                    f'</a>'
                f'</div>'
                f'<div style="font-size:13px; color:#666; margin-top:3px;">'
                    f'⭐ {spot["rating"]} • {spot["reviews"]} reviews'
                f'</div>'
                f'<div style="font-size:12px; color:#999; margin-top:4px;">'
                    f'Best nearby bodega'
                f'</div>'
            f'</div>'
        )
    else:
        bodega_html = (
            f'<div style="font-size:13px; color:#666;">'
                f'No nearby bodegas found.'
            f'</div>'
        )

    if subway_status == "On time":
        status_bg = "#e8f5e9"
        status_color = "#2e7d32"
    elif subway_status == "Minor delays":
        status_bg = "#fff8e1"
        status_color = "#f57c00"
    else:
        status_bg = "#ffebee"
        status_color = "#c62828"

    return (
        f'<div class="card">'
            f'<div style="font-weight:900; font-size:18px; margin-bottom:14px;">📍 Live Around Destination</div>'

            f'<div style="background:#fafafa; border:1px solid #ececec; border-radius:14px; padding:12px; margin-bottom:10px;">'
                f'<div style="font-weight:800; margin-bottom:6px;">☕ Nearby Coffee</div>'
                f'{coffee_html}'
            f'</div>'

            f'<div style="background:#fafafa; border:1px solid #ececec; border-radius:14px; padding:12px; margin-bottom:10px;">'
                f'<div style="font-weight:800; margin-bottom:6px;">🥯 Nearby Bagels</div>'
                f'{bagel_html}'
            f'</div>'

            f'<div style="background:#fafafa; border:1px solid #ececec; border-radius:14px; padding:12px; margin-bottom:10px;">'
                f'<div style="font-weight:800; margin-bottom:6px;">🛒 Nearby Bodega</div>'
                f'{bodega_html}'
            f'</div>'

        f'<div style="background:#fafafa; border:1px solid #ececec; border-radius:14px; padding:12px; margin-bottom:10px;">'
            f'<div style="font-weight:800;">{weather["icon"]} Weather</div>'

            f'<div style="font-size:15px; font-weight:700; margin-top:6px;">'
                f'{weather["condition"]}'
            f'</div>'

            f'<div style="font-size:13px; color:#666; margin-top:4px;">'
                f'{weather["detail"]}'
            f'</div>'

            f'<div style="font-size:12px; color:#999; margin-top:6px;">'
                f'Feels like {weather["feels_like"]}° at arrival ({weather["arrival_time"]})'
            f'</div>'
        f'</div>'

            f'<div style="background:#fafafa; border:1px solid #ececec; border-radius:14px; padding:12px;">'
                f'<div style="font-weight:800;">🚇 Transit</div>'
                f'<div style="margin-top:8px;">'
                    f'<span style="background:{status_bg}; color:{status_color}; '
                    f'padding:5px 10px; border-radius:999px; '
                    f'font-size:12px; font-weight:900;">'
                        f'{subway_status}'
                    f'</span>'
                f'</div>'
                f'<div style="font-size:12px; color:#999; margin-top:4px;">{subway_detail}</div>'
                f'<div style="font-size:12px; color:#999; margin-top:4px;">Delay added: {subway_delay_minutes} min</div>'
            f'</div>'
        f'</div>'
    )

    

def render_taxi_map(route_points, origin, destination, origin_input, destination_input):
    st.markdown(
        f'<div class="card" style="padding-bottom:10px;">'
            f'<div style="font-weight:900; font-size:18px; margin-bottom:10px;">'
                f'🚕 Taxi Route Preview'
            f'</div>',
        unsafe_allow_html=True
    )

    route_df = pd.DataFrame(route_points, columns=["lat", "lon"])

    path_data = [{
        "path": route_df[["lon", "lat"]].values.tolist(),
        "name": "Taxi route"
    }]

    min_lat = route_df["lat"].min()
    max_lat = route_df["lat"].max()
    min_lon = route_df["lon"].min()
    max_lon = route_df["lon"].max()

    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    max_span = max(max_lat - min_lat, max_lon - min_lon)

    if max_span < 0.035:
        zoom = 12.2
    elif max_span < 0.06:
        zoom = 11.5
    elif max_span < 0.10:
        zoom = 10.8
    elif max_span < 0.18:
        zoom = 10.1
    else:
        zoom = 9.5

    glow_layer = pdk.Layer(
        "PathLayer",
        data=path_data,
        get_path="path",
        get_width=10,
        width_units="pixels",
        get_color=[255, 199, 44, 70],
        pickable=False,
    )

    route_layer = pdk.Layer(
        "PathLayer",
        data=path_data,
        get_path="path",
        get_width=5,
        width_units="pixels",
        get_color=[255, 170, 0, 255],
        pickable=False,
    )

    point_layer = pdk.Layer(
        "ScatterplotLayer",
        data=[
            {"lat": origin["latitude"], "lon": origin["longitude"], "label": origin_input},
            {"lat": destination["latitude"], "lon": destination["longitude"], "label": destination_input},
        ],
        get_position="[lon, lat]",
        get_radius=7,
        radius_units="pixels",
        get_fill_color=[17, 17, 17, 255],
        get_line_color=[255, 199, 44, 255],
        line_width_min_pixels=3,
        stroked=True,
        filled=True,
        pickable=True,
    )

    try:
        taxi_icon_url = image_to_data_url("assets/nyc_taxi.png")
        taxi_marker_data = [{
            "lat": route_df.iloc[len(route_df) // 2]["lat"],
            "lon": route_df.iloc[len(route_df) // 2]["lon"],
            "icon_data": {
                "url": taxi_icon_url,
                "width": 1024,
                "height": 1024,
                "anchorY": 512,
            },
        }]

        taxi_layer = pdk.Layer(
            "IconLayer",
            data=taxi_marker_data,
            get_icon="icon_data",
            get_position="[lon, lat]",
            get_size=4,
            size_scale=12,
            pickable=True,
        )
    except Exception:
        taxi_layer = pdk.Layer(
            "ScatterplotLayer",
            data=[{
                "lat": route_df.iloc[len(route_df) // 2]["lat"],
                "lon": route_df.iloc[len(route_df) // 2]["lon"],
            }],
            get_position="[lon, lat]",
            get_radius=12,
            radius_units="pixels",
            get_fill_color=[255, 199, 44, 255],
            pickable=False,
        )

    deck = pdk.Deck(
        layers=[glow_layer, route_layer, point_layer, taxi_layer],
        initial_view_state=pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=zoom,
            pitch=0,
        ),
        tooltip={"text": "{label}"},
        map_style="light",
    )

    st.pydeck_chart(deck, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_subway_map(subway_data):
    st.markdown(
        f'<div class="card" style="padding-bottom:10px;">'
            f'<div style="font-weight:900; font-size:18px; margin-bottom:10px;">'
                f'🚇 Subway Route Preview'
            f'</div>',
        unsafe_allow_html=True
    )

    subway_layers = []
    all_points = []

    for leg in subway_data.get("transit_legs", []):
        if leg.get("vehicle_type") != "SUBWAY":
            continue

        leg_polyline = leg.get("polyline", "")
        if not leg_polyline:
            continue

        leg_points = decode_polyline(leg_polyline)
        if not leg_points:
            continue

        all_points.extend(leg_points)

        line_symbol = leg.get("line", "").split("/")[0].split(" ")[0]
        hex_color = LINE_COLORS.get(line_symbol, "#0039A6")
        rgb = hex_to_rgb(hex_color)

        leg_df = pd.DataFrame(leg_points, columns=["lat", "lon"])

        subway_layers.append(
            pdk.Layer(
                "PathLayer",
                data=[{
                    "path": leg_df[["lon", "lat"]].values.tolist(),
                    "name": leg.get("line", "Subway")
                }],
                get_path="path",
                get_width=10,
                width_units="pixels",
                get_color=[rgb[0], rgb[1], rgb[2], 255],
                pickable=False,
            )
        )

    if not all_points:
        st.markdown("</div>", unsafe_allow_html=True)
        return

    subway_df = pd.DataFrame(all_points, columns=["lat", "lon"])

    main_line = subway_data.get("line", "").split("/")[0].split(" ")[0]
    main_color = LINE_COLORS.get(main_line, "#0039A6")
    main_rgb = hex_to_rgb(main_color)

    subway_icon_url = image_to_data_url("assets/subway_car.png")

    subway_train_data = [{
        "lat": subway_df.iloc[len(subway_df) // 2]["lat"],
        "lon": subway_df.iloc[len(subway_df) // 2]["lon"],
        "icon_data": {
            "url": subway_icon_url,
            "width": 1024,
            "height": 1024,
            "anchorY": 512,
        },
    }]

    subway_train_layer = pdk.Layer(
        "IconLayer",
        data=subway_train_data,
        get_icon="icon_data",
        get_position="[lon, lat]",
        get_size=4,
        size_scale=14,
        pickable=False,
    )

    min_lat = subway_df["lat"].min()
    max_lat = subway_df["lat"].max()
    min_lon = subway_df["lon"].min()
    max_lon = subway_df["lon"].max()

    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    max_span = max(max_lat - min_lat, max_lon - min_lon)

    if max_span < 0.035:
        zoom = 12.2
    elif max_span < 0.06:
        zoom = 11.5
    elif max_span < 0.10:
        zoom = 10.8
    elif max_span < 0.18:
        zoom = 10.1
    else:
        zoom = 9.5

    subway_deck = pdk.Deck(
        layers=[*subway_layers, subway_train_layer],
        initial_view_state=pdk.ViewState(
            latitude=subway_df["lat"].mean(),
            longitude=subway_df["lon"].mean(),
            zoom=zoom,
            pitch=0,
        ),
        map_style="light",
    )

    st.pydeck_chart(subway_deck, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

current_time = datetime.now().strftime("%I:%M %p")

st.markdown(f"""
<div class="app-header">
    <div>
        <div class="app-title">RouteIQ-NYC 🚕</div>
        <div class="app-subtitle">Know when to leave. Know how to get there.</div>
    </div>
    <div class="update">
        Live NYC routing • Updated {current_time}
    </div>
</div>
""", unsafe_allow_html=True)


left, main, right = st.columns([1.05, 2.1, 1.15], gap="large")


with left:
    st.markdown("""
    <div class="card">
        <div class="section-title">🧾 Plan Your Trip</div>
        <div class="small-muted" style="margin-bottom:12px;">
            Set your route, compare the options, and know when to move.
        </div>
    </div>
    """, unsafe_allow_html=True)

    origin_input = st_searchbox(

        search_nyc_places,
        placeholder="Where are you?",
        label="Origin",
        key="origin_searchbox",
    )

    destination_input = st_searchbox(
        search_nyc_places,
        placeholder="Where to?",
        label="Destination",
        key="destination_searchbox",
    )

    arrival_mode = st.radio(
        "Arrival mode",
        ["Leave now", "Arrive by"],
        horizontal=True
    )

    if arrival_mode == "Arrive by":
        arrival_time = st.time_input("Arrive by time")
    else:
        arrival_time = None

    priority = st.selectbox(
        "Priority",
        ["fastest", "cheapest", "balanced"]
    )

    run = st.button(
        "Compare Routes",
        disabled=not (origin_input and destination_input)
    )

    st.markdown(
        f'<div class="card">'
            f'<div style="font-weight:900; margin-bottom:6px;">⚡ Real-time. Not guesses.</div>'
            f'<div class="small-muted">RouteIQ compares subway status, traffic, and ETA so you know exactly when to go.</div>'
        f'</div>'
        f'<div class="card">'
            f'<div style="font-weight:900; margin-bottom:6px;">🚇 Built for New Yorkers.</div>'
            f'<div class="small-muted">Made in NYC 💛</div>'
        f'</div>',
        unsafe_allow_html=True
    )


if run:
    user_ip = st.query_params.get("ip", ["anonymous"])[0]

    if is_rate_limited(user_ip):
        st.error("Daily RouteIQ limit reached. Please try again tomorrow.")
        st.stop()

    IP_REQUEST_LOG[user_ip].append(str(date.today()))


    if st.session_state.route_requests >= MAX_ROUTE_REQUESTS:
        st.error("RouteIQ demo limit reached for this session. Please refresh later.")
        st.stop()

    if len(origin_input) > 120 or len(destination_input) > 120:
        st.error("Please enter a shorter NYC address or place name.")
        st.stop()

    st.session_state.route_requests += 1

    now = datetime.now()

    if arrival_mode == "Leave now":
        arrival_deadline = 45
        departure_datetime_utc = datetime.now(timezone.utc)

    else:
        target = datetime.combine(now.date(), arrival_time)

        if target <= now:
            target = target + timedelta(days=1)

        arrival_deadline = round((target - now).total_seconds() / 60)

        selected_eta_guess = 20
        departure_datetime_local = target - timedelta(minutes=selected_eta_guess)
        departure_datetime_utc = departure_datetime_local.astimezone(timezone.utc)

    with st.spinner("🚇 Checking subway delays... 🚕 Reading traffic... 🧠 Comparing routes..."):
        origin = geocode_address(origin_input)
        destination = geocode_address(destination_input)

        if origin:
            origin["label"] = origin_input

        if destination:
            destination["label"] = destination_input

        if not origin or not destination:
            st.error("Couldn’t find one of those locations. Try a more specific NYC address.")
            st.stop()

        taxi_data = get_drive_eta(origin, destination)

        if not isinstance(taxi_data, dict):
            st.error("Taxi route unavailable. Try a different NYC address or time.")
            st.stop()

        subway_data = get_transit_eta(
            origin,
            destination,
            departure_time=departure_datetime_utc
        )

        if not isinstance(subway_data, dict):
            st.error("Subway route unavailable. Try a different NYC address or time.")
            st.stop()

        route_steps = subway_data.get("route_steps", [])

        subway_eta = round(subway_data["eta_seconds"] / 60)
        taxi_eta_min = round(taxi_data["eta_seconds"] / 60)
        polyline = taxi_data.get("polyline", "")

        taxi = {
            "eta": taxi_eta_min,
            "cost": 25,
            "pickup_time": 2,
            "drive_time": max(0, taxi_eta_min - 2),
            "traffic_level": "Moderate",
        }

        subway = {
            "eta": subway_eta,
            "cost": 3,
            "walk_to_station": subway_data["walk_minutes"],
            "wait_time": 0,
            "ride_time": subway_data["ride_minutes"],
            "transfers": subway_data["transfers"],
            "delay_status": subway_data["delay_status"],
        }

        coffee_spots = get_nearby_coffee(destination)
        bagel_spot = get_best_nearby_bagel(destination)
        bodega_spot = get_best_nearby_bodega(destination)

        result = make_decision(subway, taxi, arrival_deadline, priority, "clear")

        recommendation = result["recommendation"]

        selected_eta = subway["eta"] if recommendation == "subway" else taxi["eta"]

        weather_data = get_weather_at_arrival(
            destination["latitude"],
            destination["longitude"],
            selected_eta
        )

        live_html = build_live_destination_html(
            destination_input,
            weather_data,
            subway_data.get("delay_status", "On time"),
            subway_data.get("delay_detail", "No active delays reported"),
            subway_data.get("delay_minutes", 0),
            coffee_spots,
            bagel_spot,
            bodega_spot
        )

        decision_text = "🚇 Take the Subway" if recommendation == "subway" else "🚕 Take the Taxi"

        why = generate_reasoning(recommendation, subway, taxi, priority, "clear")

        route_steps_html = "".join(
            (
                f'<div style="display:flex; align-items:flex-start; gap:9px; font-size:13px; '
                f'color:#333; margin-bottom:8px; line-height:1.35;">'
                    f'<div style="width:23px; text-align:center; font-size:15px; flex-shrink:0;">'
                        f'{"👣" if step["type"] == "walk" else "🔁" if step["type"] == "transfer" else "🚇"}'
                    f'</div>'
                    f'<div style="flex:1;">{step["text"]}</div>'
                f'</div>'
            )
            for step in route_steps
        )

        line_badges_html = get_line_badges_html(subway_data)
        train_boxes_html = build_train_boxes_html(subway_data)

        subway_route_points = []

        for leg in subway_data.get("transit_legs", []):
            leg_polyline = leg.get("polyline", "")
            if leg.get("vehicle_type") == "SUBWAY" and leg_polyline:
                subway_route_points.extend(decode_polyline(leg_polyline))

        route_points = decode_polyline(polyline) if polyline else [
            (origin["latitude"], origin["longitude"]),
            (destination["latitude"], destination["longitude"]),
        ]

    with left:
        st.markdown(live_html, unsafe_allow_html=True)

    with main:
        hero_html = build_hero_card(decision_text, subway, taxi, result)
        st.markdown(hero_html, unsafe_allow_html=True)

        summary_chips_html = (
            f'<div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; margin-bottom:14px;">'
                f'<div style="background:#ffffff; border:1px solid #ececec; border-radius:16px; padding:14px; text-align:center;">'
                    f'<div style="font-size:18px;">🚇</div>'
                    f'<div style="font-size:20px; font-weight:900;">{subway["eta"]} min</div>'
                    f'<div style="font-size:11px; color:#666; font-weight:700;">Subway</div>'
                f'</div>'
                f'<div style="background:#ffffff; border:1px solid #ececec; border-radius:16px; padding:14px; text-align:center;">'
                    f'<div style="font-size:18px;">🚕</div>'
                    f'<div style="font-size:20px; font-weight:900;">{taxi["eta"]} min</div>'
                    f'<div style="font-size:11px; color:#666; font-weight:700;">Taxi</div>'
                f'</div>'
                f'<div style="background:#ffffff; border:1px solid #ececec; border-radius:16px; padding:14px; text-align:center;">'
                    f'<div style="font-size:18px;">💰</div>'
                    f'<div style="font-size:20px; font-weight:900;">${abs(taxi["cost"] - subway["cost"])}</div>'
                    f'<div style="font-size:11px; color:#666; font-weight:700;">Difference</div>'
                f'</div>'
            f'</div>'
        )

        st.markdown(summary_chips_html, unsafe_allow_html=True)

        if recommendation == "taxi":
            render_taxi_map(route_points, origin, destination, origin_input, destination_input)

        if recommendation == "subway" and subway_route_points:
            render_subway_map(subway_data)
        if subway["delay_status"] == "On time":
            chip_bg = "#e8f5e9"
            chip_color = "#2e7d32"
        elif subway["delay_status"] == "Minor delays":
            chip_bg = "#fff8e1"
            chip_color = "#f57c00"
        else:
            chip_bg = "#ffebee"
            chip_color = "#c62828"

        subway_html = (
            f'<div class="card">'
                f'<div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px; margin-bottom:10px;">'
                    f'<div style="font-weight:900; display:flex; align-items:center; flex-wrap:wrap;">🚇 Subway{line_badges_html}</div>'
                    f'<div style="background:{chip_bg}; color:{chip_color}; padding:5px 10px; border-radius:999px; '
                    f'font-size:12px; font-weight:900; white-space:nowrap;">{subway["delay_status"]}</div>'
                f'</div>'
                f'{train_boxes_html}'
                f'<div style="margin-top:14px;">'
                    f'<div class="metric"><span>ETA</span><b>{subway["eta"]} min</b></div>'
                    f'<div class="metric"><span>Cost</span><b>${subway["cost"]}</b></div>'
                    f'<div class="metric"><span>Walk</span><b>{subway["walk_to_station"]} min</b></div>'
                    f'<div class="metric"><span>Ride</span><b>{subway["ride_time"]} min</b></div>'
                    f'<div class="metric"><span>Transfers</span><b>{subway["transfers"]}</b></div>'
                f'</div>'
                f'<div style="margin-top:14px; border-top:1px solid #eee; padding-top:12px;">'
                    f'<div style="font-weight:900; font-size:14px; margin-bottom:8px;">Your route</div>'
                    f'{route_steps_html}'
                f'</div>'
            f'</div>'
        )

        st.markdown(subway_html, unsafe_allow_html=True)

        with right:
            if recommendation == "subway":
                primary_side_html = (
                    f'<div class="card">'
                        f'<div style="font-weight:900; margin-bottom:10px;">🚇 Subway</div>'
                        f'<div class="metric"><span>ETA</span><b>{subway["eta"]} min</b></div>'
                        f'<div class="metric"><span>Cost</span><b>${subway["cost"]}</b></div>'
                        f'<div class="metric"><span>Walk</span><b>{subway["walk_to_station"]} min</b></div>'
                        f'<div class="metric"><span>Ride</span><b>{subway["ride_time"]} min</b></div>'
                        f'<div class="metric"><span>Status</span><b>{subway["delay_status"]}</b></div>'
                    f'</div>'
                )
            else:
                primary_side_html = (
                    f'<div class="card">'
                        f'<div style="font-weight:900; margin-bottom:10px;">🚕 Taxi</div>'
                        f'<div class="metric"><span>ETA</span><b>{taxi["eta"]} min</b></div>'
                        f'<div class="metric"><span>Cost</span><b>${taxi["cost"]}</b></div>'
                        f'<div class="metric"><span>Pickup</span><b>{taxi["pickup_time"]} min</b></div>'
                        f'<div class="metric"><span>Drive</span><b>{taxi["drive_time"]} min</b></div>'
                        f'<div class="metric"><span>Traffic</span><b>{taxi["traffic_level"]}</b></div>'
                    f'</div>'
                )

            st.markdown(primary_side_html, unsafe_allow_html=True)

            confidence_value = get_confidence_score(result["confidence"])

            risk_level = (
                "Low" if confidence_value >= 75
                else "Medium" if confidence_value >= 45
                else "High"
            )

            worst_case = taxi["eta"] + 8 if recommendation == "taxi" else subway["eta"] + 12

            confidence_html = (
                f'<div class="card">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">'
                        f'<div style="font-weight:900;">🛡 Reliability</div>'
                        f'<div style="background:#e8f5e9; color:#2e7d32; padding:7px 12px; '
                        f'border-radius:14px; font-size:19px; font-weight:900;">{confidence_value}%</div>'
                    f'</div>'
                    f'<div style="margin-top:6px; line-height:1.6;"><b>Late risk:</b> {risk_level}</div>'
                    f'<div style="margin-top:6px; line-height:1.6;"><b>Buffer:</b> {result["buffer"]} min</div>'
                    f'<div style="margin-top:6px; line-height:1.6;"><b>Worst case:</b> {worst_case} min</div>'
                f'</div>'
            )

            st.markdown(confidence_html, unsafe_allow_html=True)

            why_html = (
                f'<div class="why-card">'
                    f'<div style="font-weight:900; margin-bottom:8px;">Why this recommendation?</div>'
                    f'<div style="margin-top:8px; line-height:1.65; color:#263447;">{why}</div>'
                f'</div>'
            )

            st.markdown(why_html, unsafe_allow_html=True)

else:
    with main:
        st.markdown(
            f'<div class="card">'
                f'<div style="font-weight:900; margin-bottom:6px;">Start with a route</div>'
                f'<div class="small-muted">RouteIQ will compare subway and taxi options using live routing data, service conditions, and AI reasoning.</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with right:
        st.markdown(
            f'<div class="card">'
                f'<div style="font-weight:900; margin-bottom:6px;">Decision Intelligence</div>'
                f'<div class="small-muted">The next version of RouteIQ is becoming a desktop urban decision workspace — not just a transit app.</div>'
            f'</div>',
            unsafe_allow_html=True
        )


st.markdown(
    f'<div class="card">'
        f'<div class="footer-grid">'
            f'<div class="footer-item">'
                f'<div style="font-weight:900;">🚇 Live subway status</div>'
                f'<div class="small-muted">via MTA</div>'
            f'</div>'
            f'<div class="footer-item">'
                f'<div style="font-weight:900;">🚕 Traffic updates</div>'
                f'<div class="small-muted">via Google</div>'
            f'</div>'
            f'<div class="footer-item">'
                f'<div style="font-weight:900;">⚙️ Route planning</div>'
                f'<div class="small-muted">via Google Maps</div>'
            f'</div>'
        f'</div>'
    f'</div>',
    unsafe_allow_html=True
)