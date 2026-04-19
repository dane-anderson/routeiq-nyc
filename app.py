import streamlit as st
from streamlit.components.v1 import html
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

st.markdown(
    """
<style>
body {
    background-color: #FFFFFF;
}

h1 {
    color: #111111;
    font-weight: 800;
}

h2, h3 {
    color: #333333;
}

.stButton > button {
    background-color: #FFC72C;
    color: black;
    font-weight: 600;
    border-radius: 8px;
    padding: 0.6em 1.2em;
    border: none;
}

.stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
    border-radius: 8px;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
# RouteIQ-NYC 🚕
### Know when to leave. Know how to get there.

Smart NYC travel decisions — subway vs taxi in real time.
""",
    unsafe_allow_html=True,
)


def build_mta_sign(symbol: str, destination: str, subtitle: str) -> str:
    color = LINE_COLORS.get(symbol, "#000000")

    return f"""<div style="
background: black;
position: relative;
border-radius: 0px;
margin-top: 6px;
margin-bottom: 6px;
max-width: 420px;
width: width: 420px;
overflow: hidden;
">
    <div style="position:absolute; top:3px; left:0; right:0; height:1px; background:white;"></div>

    <div style="
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        color: white;
        font-family: Helvetica, Arial, sans-serif;
    ">
        <div style="
            background: {color};
            color: white;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 22px;
            flex-shrink: 0;
        ">
            {symbol}
        </div>

        <div style="display:flex; flex-direction:column; justify-content:center;">
            <div style="
                font-size: 16px;
                font-weight: 800;
                line-height: 1.0;
                letter-spacing: -0.3px;
                margin: 0;
                padding: 0;
            ">
                {destination}
            </div>

            <div style="
                font-size: 10px;
                opacity: 0.85;
                font-weight: 500;
                margin-top: 2px;
                line-height: 1.1;
            ">
                {subtitle}
            </div>
        </div>
    </div>
</div>""".strip()


def render_subway_signs(subway: dict) -> None:
    transit_legs = subway.get("transit_legs", [])

    if transit_legs:
        for leg in transit_legs:
            leg_line = leg.get("line", "")
            leg_symbol = leg_line.split(" ")[0] if leg_line else ""
            leg_destination = leg.get("arrival", "Destination")
            leg_subtitle = (
                leg_line
                .replace(f"{leg_symbol} Train ", "")
                .replace("(", "")
                .replace(")", "")
            )

            html(
                build_mta_sign(
                    symbol=leg_symbol,
                    destination=leg_destination,
                    subtitle=leg_subtitle,
                ),
                height=74,
                scrolling=False,
            )
    else:
        line_name = subway.get("line", "")
        line_symbol = line_name.split(" ")[0] if line_name else ""
        destination = subway.get("arrival", "Destination")
        subtitle = (
            line_name
            .replace(f"{line_symbol} Train ", "")
            .replace("(", "")
            .replace(")", "")
        )

        html(
            build_mta_sign(
                symbol=line_symbol,
                destination=destination,
                subtitle=subtitle,
            ),
            height=74,
            scrolling=False,
        )
  



def render_route_card(subway: dict) -> None:
    walk_to = subway.get("departure", "N/A")
    get_off = subway.get("arrival", "N/A")
    transit_legs = subway.get("transit_legs", [])

    route_html = f"""
    <div style="
        background-color: #f7f7f7;
        padding: 14px 16px;
        border-radius: 12px;
        border: 1px solid #e6e6e6;
        margin-top: 10px;
        margin-bottom: 10px;
        max-width: 430px;
        width: fit-content;
        line-height: 1.7;
    ">
        🚶 <b>Walk to:</b> {walk_to}<br>
    """

    if transit_legs:
        for leg in transit_legs:
            route_html += (
                f"🚇 <b>Take:</b> {leg.get('line', 'Train')} "
                f"({leg['departure']} → {leg['arrival']})<br>"
            )
    else:
        route_html += f"🚇 <b>Take:</b> {subway.get('line', 'Train')}<br>"

    route_html += f"""📍 <b>Get off at:</b> {get_off}
    </div>
    """

    st.markdown(route_html, unsafe_allow_html=True)


col1, col2 = st.columns([1, 1.2])

with col1:
    st.markdown("### Plan Your Trip")

    origin_input = st.text_input("Enter starting address", "Times Square, NYC")
    destination_input = st.text_input("Enter destination", "Wall Street, NYC")

    arrival_deadline = st.number_input(
        "Must arrive within how many minutes?",
        min_value=1,
        value=45,
    )

    priority = st.selectbox("Priority", ["fastest", "cheapest", "balanced"])

    run = st.button("Make Decision")

with col2:
    if run:
        origin = geocode_address(origin_input)
        destination = geocode_address(destination_input)

        if not origin or not destination:
            st.error("Could not find one of the locations.")
            st.stop()

        with st.spinner("Analyzing routes..."):
            taxi_eta = get_drive_eta(origin, destination)
            subway_data = get_transit_eta(origin, destination)

        if not subway_data or subway_data == 9999 or not isinstance(subway_data, dict):
            st.error("No transit route found.")
            st.stop()

        subway_eta = round(subway_data["eta_seconds"] / 60)
        delay_status = subway_data["delay_status"]

        if delay_status == "Severe delays":
            subway_eta += 10
        elif delay_status == "Minor delays":
            subway_eta += 5

        taxi_eta_min = round(taxi_eta / 60)

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
            "line": subway_data.get("line"),
            "departure": subway_data.get("departure"),
            "arrival": subway_data.get("arrival"),
            "transit_legs": subway_data.get("transit_legs", []),
        }

        weather = "clear"

        result = make_decision(subway, taxi, arrival_deadline, priority, weather)
        why = generate_reasoning(result, subway, taxi, priority, weather)

        recommendation = result["recommendation"]

        if recommendation == "subway":
            decision_icon = "🚇"
            decision_text = "Take the Subway"
            card_bg = "#111111"
            card_text = "white"
        else:
            decision_icon = "🚕"
            decision_text = "Take the Taxi"
            card_bg = "#FFC72C"
            card_text = "black"

        st.markdown(
            f"""
            <div style="
                background-color: {card_bg};
                color: {card_text};
                padding: 20px;
                border-radius: 14px;
                text-align: center;
                font-size: 26px;
                font-weight: 700;
                margin-bottom: 15px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.12);
            ">
                {decision_icon} {decision_text}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Trip Comparison")

        compare_col1, compare_col2 = st.columns(2)

        with compare_col1:
            st.markdown("#### 🚇 Subway")
            st.write(f"ETA: {subway['eta']} min")
            st.write(f"Cost: ${subway['cost']:.2f}")
            st.write(f"Walk: {subway['walk_to_station']} min")
            st.write(f"Wait: {subway['wait_time']} min")
            st.write(f"Ride: {subway['ride_time']} min")
            st.write(f"Transfers: {subway['transfers']}")
            st.write(f"Status: {subway['delay_status']}")

            render_subway_signs(subway)

            st.markdown("### 🚶 Your Route")
            render_route_card(subway)

            if result["leave_in"] > 0:
                label = "🚇 Leave in" if result["recommendation"] == "subway" else "🚕 Leave in"

                st.markdown(
                    f"""
                    <div style="
                        display: inline-block;
                        background-color: #d4edda;
                        color: #155724;
                        padding: 8px 14px;
                        border-radius: 10px;
                        font-weight: 600;
                        margin-top: 10px;
                    ">
                        {label} {result['leave_in']} minutes
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div style="
                        display: inline-block;
                        background-color: #f8d7da;
                        color: #721c24;
                        padding: 8px 14px;
                        border-radius: 10px;
                        font-weight: 600;
                        margin-top: 10px;
                    ">
                        🚨 Leave NOW
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with compare_col2:
            st.markdown("#### 🚕 Taxi")
            st.write(f"ETA: {taxi['eta']} min")
            st.write(f"Cost: ${taxi['cost']:.2f}")
            st.write(f"Pickup: {taxi['pickup_time']} min")
            st.write(f"Drive: {taxi['drive_time']} min")
            st.write(f"Traffic: {taxi['traffic_level']}")

        st.markdown("### Why")
        st.info(why)

        st.markdown("### Confidence")
        st.write(result["confidence"])
        buffer_display = max(result["buffer"], 0)
        st.write(f"Buffer: {buffer_display} minutes")