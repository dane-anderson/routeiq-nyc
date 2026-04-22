import streamlit as st
from decision_engine import make_decision
from ai_voice import generate_reasoning
from routes_api import get_drive_eta, get_transit_eta, geocode_address

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

st.set_page_config(page_title="RouteIQ-NYC", page_icon="🚕", layout="wide")

# -----------------------
# STYLE
# -----------------------
st.markdown("""
<style>
.block-container { padding: 1.5rem 2rem; }

.card {
    background: #ffffff;
    border-radius: 18px;
    padding: 18px;
    border: 1px solid #eee;
}
            
.why-card {
    background: #eaf1fb;
    border-radius: 18px;
    padding: 18px;
    border: 1px solid #d9e5f5;
}

.metric {
    display:flex;
    justify-content:space-between;
    padding:6px 0;
    font-size:14px;
}

.hero {
    background:#FFC72C;
    border-radius:18px;
    padding:20px;
    display:flex;
    justify-content:space-between;
    align-items:center;
}

.update {
    color:#666;
    font-size:13px;
}
            
.stButton > button {
    background: #FFC72C !important;
    color: #111111 !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.8rem 1rem !important;
    font-size: 16px !important;
    font-weight: 800 !important;
    width: 100% !important;
    box-shadow: none !important;
}

.stButton > button:hover {
    background: #f0ba19 !important;
    color: #111111 !important;
    border: none !important;
}    

</style>
""", unsafe_allow_html=True)

# -----------------------
# HEADER HTML
# -----------------------
header_html = (
    f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">'
        f'<div>'
            f'<div style="font-size:28px; font-weight:800;">RouteIQ-NYC 🚕</div>'
            f'<div style="color:#666;">Know when to leave. Know how to get there.</div>'
        f'</div>'
        f'<div class="update">Real-time updates • just now</div>'
    f'</div>'
)

st.markdown(header_html, unsafe_allow_html=True)

# -----------------------
# LAYOUT
# -----------------------
left, right = st.columns([1,2])

# -----------------------
# LEFT PANEL
# -----------------------
with left:

    

    st.markdown(
        f'<div style="font-weight:700; font-size:18px;">🧾 Plan Your Trip</div>'
        f'<div style="font-size:13px; color:#666; margin-top:4px; margin-bottom:12px;">Set your route, compare the options, and know when to move.</div>',
        unsafe_allow_html=True
    )

   

    origin_input = st.text_input(
    "",
    placeholder="Where are you?",
    label_visibility="collapsed"
    )
    destination_input = st.text_input(
    "",
    placeholder="Where to?",
    label_visibility="collapsed"
    )

    arrival_deadline = st.number_input("Must arrive within", min_value=1, value=45)
    priority = st.selectbox("Priority", ["fastest", "cheapest", "balanced"])

    run = st.button(
    "Make Decision",
    disabled=not (origin_input.strip() and destination_input.strip())
    )

    st.markdown('</div>', unsafe_allow_html=True)



    st.markdown(
        f'<div class="card" style="margin-top:12px;">'
        f'<div style="font-weight:700; margin-bottom:6px;">⚡ Real-time. Not guesses.</div>'
        f'<div style="font-size:13px; color:#666; line-height:1.5;">We compare live subway status, traffic, and ETA so you know exactly when to go.</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="card" style="margin-top:12px;">'
        f'<div style="font-weight:700; margin-bottom:6px;">🚇 Built for New Yorkers.</div>'
        f'<div style="font-size:13px; color:#666; line-height:1.5;">Made in NYC 💛</div>'
        f'</div>',
        unsafe_allow_html=True
    )

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

    badges_html = '<span style="display:inline-flex; align-items:center; gap:8px; margin-left:10px;">'
    for symbol in symbols:
        color = "#111111"
        if symbol in ["1", "2", "3"]:
            color = "#EE352E"
        elif symbol in ["4", "5", "6"]:
            color = "#00933C"
        elif symbol == "7":
            color = "#B933AD"
        elif symbol in ["A", "C", "E"]:
            color = "#0039A6"
        elif symbol in ["B", "D", "F", "M"]:
            color = "#FF6319"
        elif symbol in ["N", "Q", "R", "W"]:
            color = "#FCCC0A"
        elif symbol in ["J", "Z"]:
            color = "#996633"
        elif symbol == "G":
            color = "#6CBE45"
        elif symbol == "L":
            color = "#A7A9AC"

        badges_html += (
            f'<span style="width:28px; height:28px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; color:white; font-size:14px; font-weight:800; background:{color};">{symbol}</span>'
        )

    badges_html += '</span>'
    return badges_html

def get_confidence_score(confidence_text: str) -> int:
    text = (confidence_text or "").lower()

    if "comfortably" in text:
        return 72
    if "good chance" in text or "likely" in text:
        return 64
    if "tight" in text or "close" in text:
        return 52
    if "risk" in text or "unlikely" in text:
        return 38
    return 60

def build_train_boxes_html(subway_data: dict) -> str:
    transit_legs = subway_data.get("transit_legs", [])

    if not transit_legs:
        line_text = subway_data.get("line", "")
        if not line_text:
            return ""

        symbol = line_text.split(" ")[0]
        destination = subway_data.get("arrival", "Destination")
        subtitle = line_text.replace(f"{symbol} Train ", "").replace("(", "").replace(")", "")
        transit_legs = [{"line": line_text, "arrival": destination, "subtitle": subtitle}]

    boxes_html = '<div style="margin-top:14px; display:flex; flex-direction:column; gap:10px;">'

    for leg in transit_legs:
        line_text = leg.get("line", "")
        if not line_text:
            continue

        symbol = line_text.split(" ")[0]
        destination = leg.get("arrival", "Destination")
        subtitle = line_text.replace(f"{symbol} Train ", "").replace("(", "").replace(")", "")
        color = LINE_COLORS.get(symbol, "#111111")
        text_color = "#111111" if color == "#FCCC0A" else "#FFFFFF"

        boxes_html += (
            f'<div style="background:#111111; border-radius:14px; padding:12px 14px; display:flex; align-items:center; gap:12px;">'
                f'<div style="width:34px; height:34px; border-radius:50%; background:{color}; color:{text_color}; display:flex; align-items:center; justify-content:center; font-size:16px; font-weight:800; flex-shrink:0;">{symbol}</div>'
                f'<div style="display:flex; flex-direction:column; gap:2px;">'
                    f'<div style="color:#FFFFFF; font-size:16px; font-weight:800; line-height:1;">{destination}</div>'
                    f'<div style="color:#D1D5DB; font-size:11px; font-weight:600; line-height:1.2;">{subtitle}</div>'
                f'</div>'
            f'</div>'
        )

    boxes_html += '</div>'
    return boxes_html

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
    points = decode_polyline(polyline)
    context_labels = get_nyc_context_labels(points)

    if len(points) < 2:
        points = [
            (origin["latitude"], origin["longitude"]),
            (destination["latitude"], destination["longitude"]),
        ]

    lats = [p[0] for p in points]
    lons = [p[1] for p in points]

    min_lat = min(lats)
    max_lat = max(lats)
    min_lon = min(lons)
    max_lon = max(lons)

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
    f'font-size="12" '
    f'font-weight="700" '
    f'fill={"#9AA3AF" if label["kind"] == "water" else "#A8ADB4"} '
    f'opacity="0.75" '
    f'text-anchor="middle">'
    f'{label["name"]}'
    f'</text>'
    for label in scaled_context_labels
)

    return (
    f'<div style="margin-top:14px; background:#F7F7F5; border:1px solid #ECE8DE; border-radius:14px; height:136px; position:relative; overflow:hidden;">'

        f'<div style="position:absolute; inset:0; background:linear-gradient(90deg, rgba(0,0,0,0.03) 1px, transparent 1px), linear-gradient(rgba(0,0,0,0.03) 1px, transparent 1px); background-size:36px 36px;"></div>'

        f'<svg viewBox="0 0 520 160" style="position:absolute; inset:0; width:100%; height:100%;">'

            f'{labels_svg}'

            f'<path d="{path_d}" stroke="#F4BC1C" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round" />'
            f'<circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="6" fill="#FFFFFF" stroke="#F4BC1C" stroke-width="4" />'
            f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="6" fill="#FFFFFF" stroke="#F4BC1C" stroke-width="4" />'
            f'<text x="{taxi_x - 8:.1f}" y="{taxi_y - 6:.1f}" font-size="20">🚕</text>'

        f'</svg>'

        f'<div style="position:absolute; left:{max(start_x - 22, 10):.1f}px; top:{max(start_y - 30, 8):.1f}px; background:#111111; color:#FFFFFF; border-radius:10px; padding:5px 8px; font-size:11px; font-weight:700; max-width:120px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{origin_label}</div>'

        f'<div style="position:absolute; left:{min(end_x - 22, 380):.1f}px; top:{min(end_y + 10, 105):.1f}px; background:#111111; color:#FFFFFF; border-radius:10px; padding:5px 8px; font-size:11px; font-weight:700; max-width:130px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{destination_label}</div>'

    f'</div>'
)

# -----------------------
# RIGHT PANEL
# -----------------------
with right:

    if run:

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
        polyline = taxi_data["polyline"]

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

        route_steps_html = ""

        for step in route_steps:
            icon = "👣" if step["type"] == "walk" else "🚇"

        route_steps_html = "".join(
(
    f'<div style="display:flex; align-items:center; gap:8px; font-size:13px; color:#333; margin-bottom:6px;">'
        f'<div style="width:22px; text-align:center; font-size:14px;">'
            f'{"👣" if step["type"] == "walk" else "🔁" if step["type"] == "transfer" else "🚇"}'
        f'</div>'
        f'<div style="flex:1;">'
            f'{step["text"]}'
        f'</div>'
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

        # -----------------------
        # HERO HTML
        # -----------------------
        hero_html = (
            f'<div class="hero">'
                f'<div style="display:flex; justify-content:space-between; align-items:center; width:100%;">'

                    f'<div>'
                        f'<div style="font-size:12px; font-weight:700; color:#4d3a00; letter-spacing:0.03em;">ROUTEIQ RECOMMENDS</div>'
                        f'<div style="font-size:26px; font-weight:800; margin-top:2px;">{decision_text}</div>'
                        f'<div style="margin-top:8px;">'
                            f'<span style="background:rgba(255,255,255,0.45); color:#4d3a00; padding:6px 12px; border-radius:999px; font-size:13px; font-weight:700; display:inline-block;">'
                                f'Saves {abs(subway["eta"] - taxi["eta"])} minutes • More predictable'
                            f'</span>'
                        f'</div>'
                    f'</div>'

                    f'<div style="text-align:right; border-left:1px solid rgba(0,0,0,0.12); padding-left:20px; margin-left:20px;">'
                        f'<div style="font-size:12px; font-weight:700; color:#4d3a00;">Leave in</div>'
                        f'<div style="font-size:34px; font-weight:800; line-height:1; margin:4px 0;">{max(result["leave_in"], 0)} min</div>'
                        f'<div style="font-size:13px; font-weight:600; color:#4d3a00;">to arrive on time</div>'
                 
                    f'</div>'

                f'</div>'
        f'</div>'
    )

        st.markdown(hero_html, unsafe_allow_html=True)

        # -----------------------
        # CARDS HTML
        # -----------------------
        subway_html = (
            f'<div class="card">'
                f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">'
                    f'<div style="font-weight:700; display:flex; align-items:center;">🚇 Subway{line_badges_html}</div>'
                    f'<div style="background:#e8f5e9; color:#2e7d32; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700;">'
                        f'{subway["delay_status"]}'
                    f'</div>'
            f'</div>'

                f'<div class="metric"><span>ETA</span><b>{subway["eta"]} min</b></div>'
                f'<div class="metric"><span>Cost</span><b>${subway["cost"]}</b></div>'
                f'<div class="metric"><span>Walk</span><b>{subway["walk_to_station"]} min</b></div>'
                f'<div class="metric"><span>Ride</span><b>{subway["ride_time"]} min</b></div>'
                f'<div class="metric"><span>Transfers</span><b>{subway["transfers"]}</b></div>'
                f'<div style="margin-top:12px; border-top:1px solid #eee; padding-top:10px;">'

                f'<div style="font-weight:700; font-size:14px; margin-bottom:6px;">Your route</div>'

                f'<div style="display:flex; flex-direction:column; gap:4px;">'
                    f'{route_steps_html}'
                f'</div>'
            f'</div>'
        )

        taxi_html = (
            f'<div class="card">'
                f'<div style="font-weight:700; margin-bottom:10px;">🚕 Taxi</div>'
                f'<div class="metric"><span>ETA</span><b>{taxi["eta"]} min</b></div>'
                f'<div class="metric"><span>Cost</span><b>${taxi["cost"]}</b></div>'
                f'<div class="metric"><span>Pickup</span><b>{taxi["pickup_time"]} min</b></div>'
                f'<div class="metric"><span>Drive</span><b>{taxi["drive_time"]} min</b></div>'
                f'<div class="metric"><span>Traffic</span><b>{taxi["traffic_level"]}</b></div>'
                f'{taxi_map_html}'
            f'</div>'
        )


        c1, c2 = st.columns(2)
        with c1:
            st.markdown(subway_html, unsafe_allow_html=True)
        with c2:
            st.markdown(taxi_html, unsafe_allow_html=True)
       

        # -----------------------
        # WHY + CONFIDENCE
        # -----------------------
        why_html = (
            f'<div class="why-card">'
                f'<div style="font-weight:700; margin-bottom:8px;"> Why this recommendation?</div>'
                f'<div style="margin-top:8px; line-height:1.65; color:#263447;">{why}</div>'
            f'</div>'
        )

        confidence_html = (
            f'<div class="card">'
                f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">'
                    f'<div style="font-weight:700;">🛡 Confidence</div>'
                    f'<div style="background:#e8f5e9; color:#2e7d32; padding:6px 12px; border-radius:12px; font-size:18px; font-weight:800;">{get_confidence_score(result["confidence"])}%</div>'
                f'</div>'
                f'<div style="margin-top:6px; line-height:1.6;">You’ll get there comfortably</div>'
                f'<div style="margin-top:8px; color:#555;">Buffer: {result["buffer"]} min</div>'
            f'</div>'
        )

        b1, b2 = st.columns([2,1])
        with b1:
            st.markdown(why_html, unsafe_allow_html=True)
        with b2:
            st.markdown(confidence_html, unsafe_allow_html=True)
        footer_html = (
            f'<div class="card" style="margin-top:12px;">'
                f'<div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:16px; text-align:center;">'

                    f'<div>'
                        f'<div style="font-weight:700;">🚇 Live subway status</div>'
                        f'<div style="font-size:13px; color:#666; margin-top:4px;">via MTA</div>'
                    f'</div>'

                    f'<div>'
                        f'<div style="font-weight:700;">🚕 Traffic updates</div>'
                        f'<div style="font-size:13px; color:#666; margin-top:4px;">via Google</div>'
                    f'</div>'

                    f'<div>'
                        f'<div style="font-weight:700;">⚙️ Route planning</div>'
                        f'<div style="font-size:13px; color:#666; margin-top:4px;">via Google Maps</div>'
                    f'</div>'

                f'</div>'
            f'</div>'
        )

        st.markdown(footer_html, unsafe_allow_html=True)

