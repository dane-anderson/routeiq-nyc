import streamlit as st
from decision_engine import make_decision
from ai_voice import generate_reasoning
from routes_api import get_drive_eta, get_transit_eta, geocode_address
from utils.confidence import get_confidence_score
from components.cards import build_train_boxes_html

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

st.set_page_config(
    page_title="RouteIQ-NYC",
    page_icon="🚕",
    layout="centered"
)

# -----------------------
# MOBILE-FIRST STYLE
# -----------------------
st.markdown("""
<style>
.block-container {
    max-width: 520px;
    padding: 3rem 1rem 2rem 1rem;
}

html, body, [class*="css"] {
    background: #fafafa;
}

.app-header {
    background: #111111;
    color: #ffffff;
    border-radius: 22px;
    padding: 22px;
    margin-bottom: 16px;
}

.app-title {
    font-size: 30px;
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
    margin-top: 14px;
    background: rgba(255,255,255,0.1);
    color: #f5f5f5;
    border-radius: 999px;
    padding: 7px 11px;
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
    padding: 20px;
    margin-bottom: 14px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.08);
}

.hero-top {
    font-size: 12px;
    font-weight: 900;
    color: #4d3a00;
    letter-spacing: 0.06em;
}

.hero-main {
    font-size: 30px;
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

.stButton > button:hover {
    background: #f0ba19 !important;
    color: #111111 !important;
    border: none !important;
}

.footer-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 12px;
}

.footer-item {
    background: #fafafa;
    border-radius: 14px;
    padding: 12px;
}

@media (min-width: 700px) {
    .block-container {
        max-width: 620px;
    }
}
</style>
""", unsafe_allow_html=True)


# -----------------------
# HELPERS
# -----------------------
def get_line_badges_html(subway_data: dict) -> str:
    transit_legs = subway_data.get("transit_legs", [])
    symbols = []

    if transit_legs:
        for leg in transit_legs:
            line_text = leg.get("line", "")
            if not line_text:
                continue
            symbol = line_text.split(" ")[0]
            if symbol and symbol not in symbols:
                symbols.append(symbol)
    else:
        line_text = subway_data.get("line", "")
        if line_text:
            symbol = line_text.split(" ")[0]
            if symbol:
                symbols.append(symbol)

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


def get_nyc_context_labels(points: list[tuple[float, float]]) -> list[dict]:
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    labels = []

    if max_lat > 40.74 and min_lat < 40.79 and max_lon > -74.01 and min_lon < -73.96:
        labels.append({"name": "Midtown", "lat": 40.754, "lon": -73.984, "kind": "area"})
        labels.append({"name": "Empire State", "lat": 40.7484, "lon": -73.9857, "kind": "landmark"})

    if min_lat < 40.73 and max_lon > -74.02 and min_lon < -73.98:
        labels.append({"name": "Lower Manhattan", "lat": 40.7128, "lon": -74.0060, "kind": "area"})
        labels.append({"name": "Wall St", "lat": 40.706, "lon": -74.009, "kind": "landmark"})

    if min_lat < 40.75 and max_lat > 40.72 and min_lon < -73.99 and max_lon > -74.01:
        labels.append({"name": "West Village", "lat": 40.735, "lon": -74.003, "kind": "landmark"})

    if min_lon > -74.02 and max_lon > -73.98 and min_lat < 40.72:
        labels.append({"name": "Brooklyn", "lat": 40.678, "lon": -73.944, "kind": "area"})

    if min_lon < -73.99 and max_lon > -73.98:
        labels.append({"name": "East River", "lat": 40.72, "lon": -73.975, "kind": "water"})

    return labels


def build_taxi_map_html(origin: dict, destination: dict, origin_label: str, destination_label: str, polyline: str) -> str:
    points = decode_polyline(polyline) if polyline else []

    if len(points) < 2:
        points = [
            (origin["latitude"], origin["longitude"]),
            (destination["latitude"], destination["longitude"]),
        ]

    context_labels = get_nyc_context_labels(points)

    lats = [p[0] for p in points]
    lons = [p[1] for p in points]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    lat_range = max(max_lat - min_lat, 0.01)
    lon_range = max(max_lon - min_lon, 0.01)

    def scale_point(lat: float, lon: float) -> tuple[float, float]:
        x = 20 + ((lon - min_lon) / lon_range) * 480
        y = 130 - ((lat - min_lat) / lat_range) * 100
        return x, y

    scaled_points = [scale_point(lat, lon) for lat, lon in points]

    scaled_context_labels = []
    for label in context_labels:
        lx, ly = scale_point(label["lat"], label["lon"])
        scaled_context_labels.append({
            "name": label["name"],
            "x": lx,
            "y": ly,
            "kind": label["kind"],
        })

    start_x, start_y = scaled_points[0]
    end_x, end_y = scaled_points[-1]

    polyline_path = " ".join(f"L {x:.1f} {y:.1f}" for x, y in scaled_points[1:])
    path_d = f"M {scaled_points[0][0]:.1f} {scaled_points[0][1]:.1f} {polyline_path}"

    taxi_idx = max(1, len(scaled_points) // 2)
    taxi_x, taxi_y = scaled_points[taxi_idx]

    labels_svg = "".join(
        f'<text x="{label["x"]:.1f}" y="{label["y"]:.1f}" '
        f'font-size="12" font-weight="800" '
        f'fill={"#9AA3AF" if label["kind"] == "water" else "#A8ADB4"} '
        f'opacity="0.75" text-anchor="middle">{label["name"]}</text>'
        for label in scaled_context_labels
    )

    return (
        f'<div style="margin-top:14px; background:#F7F7F5; border:1px solid #ECE8DE; '
        f'border-radius:16px; height:148px; position:relative; overflow:hidden;">'
            f'<div style="position:absolute; inset:0; background:linear-gradient(90deg, rgba(0,0,0,0.035) 1px, transparent 1px), '
            f'linear-gradient(rgba(0,0,0,0.035) 1px, transparent 1px); background-size:36px 36px;"></div>'

            f'<svg viewBox="0 0 520 160" style="position:absolute; inset:0; width:100%; height:100%;">'
                f'{labels_svg}'
                f'<path d="{path_d}" stroke="#F4BC1C" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round" />'
                f'<circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="6" fill="#FFFFFF" stroke="#F4BC1C" stroke-width="4" />'
                f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="6" fill="#FFFFFF" stroke="#F4BC1C" stroke-width="4" />'
                f'<text x="{taxi_x - 8:.1f}" y="{taxi_y - 6:.1f}" font-size="22">🚕</text>'
            f'</svg>'

            f'<div style="position:absolute; left:{max(start_x - 22, 10):.1f}px; top:{max(start_y - 30, 8):.1f}px; '
            f'background:#111111; color:#FFFFFF; border-radius:10px; padding:5px 8px; font-size:11px; '
            f'font-weight:800; max-width:130px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{origin_label}</div>'

            f'<div style="position:absolute; left:{min(end_x - 22, 360):.1f}px; top:{min(end_y + 10, 110):.1f}px; '
            f'background:#111111; color:#FFFFFF; border-radius:10px; padding:5px 8px; font-size:11px; '
            f'font-weight:800; max-width:140px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{destination_label}</div>'
        f'</div>'
    )


# -----------------------
# HEADER
# -----------------------
st.markdown("""
<div class="app-header">
    <div class="app-title">RouteIQ-NYC 🚕</div>
    <div class="app-subtitle">Know when to leave. Know how to get there.</div>
    <div class="update">Real-time updates • just now</div>
</div>
""", unsafe_allow_html=True)


# -----------------------
# INPUT CARD
# -----------------------
st.markdown("""
<div class="card">
    <div class="section-title">🧾 Plan Your Trip</div>
    <div class="small-muted" style="margin-bottom:12px;">
        Set your route, compare the options, and know when to move.
    </div>
</div>
""", unsafe_allow_html=True)

origin_input = st.text_input(
    "Origin",
    placeholder="Where are you?",
    label_visibility="collapsed"
)

destination_input = st.text_input(
    "Destination",
    placeholder="Where to?",
    label_visibility="collapsed"
)

arrival_deadline = st.number_input(
    "Must arrive within",
    min_value=1,
    value=45
)

priority = st.selectbox(
    "Priority",
    ["fastest", "cheapest", "balanced"]
)

run = st.button(
    "Compare Routes",
    disabled=not (origin_input.strip() and destination_input.strip())
)


# -----------------------
# RESULTS
# -----------------------
if run:
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
    subway_data = get_transit_eta(origin, destination)
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

    result = make_decision(subway, taxi, arrival_deadline, priority, "clear")
    why = generate_reasoning(result, subway, taxi, priority, "clear")

    line_badges_html = get_line_badges_html(subway_data)
    train_boxes_html = build_train_boxes_html(subway_data)
    taxi_map_html = build_taxi_map_html(origin, destination, origin_input, destination_input, polyline)

    recommendation = result["recommendation"]
    decision_text = "🚇 Take the Subway" if recommendation == "subway" else "🚕 Take the Taxi"

    hero_html = (
        f'<div class="hero">'

            f'<div class="hero-top">'
                f'ROUTEIQ RECOMMENDS'
            f'</div>'

            f'<div class="hero-main">'
                f'{decision_text}'
            f'</div>'

            f'<div class="hero-chip">'
                f'Saves {abs(subway["eta"] - taxi["eta"])} minutes • More predictable'
            f'</div>'

            f'<div class="leave-box">'

                f'<div class="leave-label">'
                    f'Leave in'
                f'</div>'

                f'<div class="leave-number">'
                    f'{max(result["leave_in"], 0)} min'
                f'</div>'

                f'<div style="font-size:13px; color:#e5e7eb; margin-top:4px;">'
                    f'to arrive on time'
                f'</div>'

            f'</div>'

        f'</div>'
    )

    st.markdown(hero_html, unsafe_allow_html=True)

    summary_chips_html = (
        f'<div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; margin-bottom:14px;">'

            f'<div style="background:#ffffff; border:1px solid #ececec; border-radius:16px; padding:12px; text-align:center;">'
                f'<div style="font-size:18px;">🚇</div>'
                f'<div style="font-size:18px; font-weight:900;">{subway["eta"]} min</div>'
                f'<div style="font-size:11px; color:#666; font-weight:700;">Subway</div>'
            f'</div>'

            f'<div style="background:#ffffff; border:1px solid #ececec; border-radius:16px; padding:12px; text-align:center;">'
                f'<div style="font-size:18px;">🚕</div>'
                f'<div style="font-size:18px; font-weight:900;">{taxi["eta"]} min</div>'
                f'<div style="font-size:11px; color:#666; font-weight:700;">Taxi</div>'
            f'</div>'

            f'<div style="background:#ffffff; border:1px solid #ececec; border-radius:16px; padding:12px; text-align:center;">'
                f'<div style="font-size:18px;">💰</div>'
                f'<div style="font-size:18px; font-weight:900;">${abs(taxi["cost"] - subway["cost"])}</div>'
                f'<div style="font-size:11px; color:#666; font-weight:700;">Difference</div>'
            f'</div>'

        f'</div>'
    )

    st.markdown(summary_chips_html, unsafe_allow_html=True)

    subway_html = (
        f'<div class="card">'
            f'<div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px; margin-bottom:10px;">'
                f'<div style="font-weight:900; display:flex; align-items:center; flex-wrap:wrap;">🚇 Subway{line_badges_html}</div>'
                f'<div style="background:#e8f5e9; color:#2e7d32; padding:5px 10px; border-radius:999px; '
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

    taxi_html = (
        f'<div class="card">'
            f'<div style="font-weight:900; margin-bottom:10px;">🚕 Taxi</div>'
            f'<div class="metric"><span>ETA</span><b>{taxi["eta"]} min</b></div>'
            f'<div class="metric"><span>Cost</span><b>${taxi["cost"]}</b></div>'
            f'<div class="metric"><span>Pickup</span><b>{taxi["pickup_time"]} min</b></div>'
            f'<div class="metric"><span>Drive</span><b>{taxi["drive_time"]} min</b></div>'
            f'<div class="metric"><span>Traffic</span><b>{taxi["traffic_level"]}</b></div>'
            f'{taxi_map_html}'
        f'</div>'
    )

    st.markdown(subway_html, unsafe_allow_html=True)
    st.markdown(taxi_html, unsafe_allow_html=True)

    why_html = (
        f'<div class="why-card">'
            f'<div style="font-weight:900; margin-bottom:8px;">Why this recommendation?</div>'
            f'<div style="margin-top:8px; line-height:1.65; color:#263447;">{why}</div>'
        f'</div>'
    )

    confidence_html = (
        f'<div class="card">'
            f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">'
                f'<div style="font-weight:900;">🛡 Confidence</div>'
                f'<div style="background:#e8f5e9; color:#2e7d32; padding:7px 12px; '
                f'border-radius:14px; font-size:19px; font-weight:900;">{get_confidence_score(result["confidence"])}%</div>'
            f'</div>'
            f'<div style="margin-top:6px; line-height:1.6;">You’ll get there comfortably</div>'
            f'<div style="margin-top:8px; color:#555;">Buffer: {result["buffer"]} min</div>'
        f'</div>'
    )

    st.markdown(why_html, unsafe_allow_html=True)
    st.markdown(confidence_html, unsafe_allow_html=True)

else:
    st.markdown(
        """
        <div class="card">
            <div style="font-weight:900; margin-bottom:6px;">⚡ Real-time. Not guesses.</div>
            <div class="small-muted">
                RouteIQ compares live subway status, traffic, and ETA so you know exactly when to go.
            </div>
        </div>

        <div class="card">
            <div style="font-weight:900; margin-bottom:6px;">🚇 Built for New Yorkers.</div>
            <div class="small-muted">Made in NYC 💛</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# -----------------------
# FOOTER
# -----------------------
st.markdown(
    """
    <div class="card">
        <div class="footer-grid">
            <div class="footer-item">
                <div style="font-weight:900;">🚇 Live subway status</div>
                <div class="small-muted">via MTA</div>
            </div>
            <div class="footer-item">
                <div style="font-weight:900;">🚕 Traffic updates</div>
                <div class="small-muted">via Google</div>
            </div>
            <div class="footer-item">
                <div style="font-weight:900;">⚙️ Route planning</div>
                <div class="small-muted">via Google Maps</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)