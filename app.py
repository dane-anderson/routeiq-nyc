
import streamlit as st
from decision_engine import make_decision
from ai_voice import generate_reasoning
from routes_api import get_drive_eta, get_transit_eta, geocode_address

st.set_page_config(page_title="RouteIQ-NYC", page_icon="🚕", layout="wide")

st.markdown("""
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

.decision-card {
    background: linear-gradient(135deg, #111111 0%, #1f1f1f 100%);
    color: white;
    padding: 1.4rem;
    border-radius: 18px;
    margin-bottom: 1rem;
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    border-left: 8px solid #FFC72C;
}

.metric-card {
    background-color: #f7f7f7;
    padding: 1rem;
    border-radius: 16px;
    border: 1px solid #e6e6e6;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    margin-bottom: 1rem;
}

.small-label {
    font-size: 0.85rem;
    color: #666666;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.big-decision {
    font-size: 2rem;
    font-weight: 800;
    margin-top: 0.2rem;
    margin-bottom: 0.4rem;
}

.reason-box {
    background-color: #fff8db;
    border-left: 6px solid #FFC72C;
    padding: 1rem;
    border-radius: 12px;
    margin-top: 1rem;
}

.confidence-pill {
    display: inline-block;
    background-color: #111111;
    color: white;
    padding: 0.35rem 0.8rem;
    border-radius: 999px;
    font-size: 0.9rem;
    font-weight: 600;
    margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
# RouteIQ-NYC 🚕
### Know when to leave. Know how to get there.

Smart NYC travel decisions — subway vs taxi in real time.
""")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.markdown("### Plan Your Trip")

    origin_input = st.text_input("Enter starting address", "Times Square, NYC")
    destination_input = st.text_input("Enter destination", "Wall Street, NYC")

    arrival_deadline = st.number_input(
        "Must arrive within how many minutes?",
        min_value=1,
        value=45
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
            subway_eta = round(subway_data["eta_seconds"] / 60)

        taxi_eta_min = round(taxi_eta / 60)
        subway_eta_min = round(subway_eta / 60)

        taxi = {
            "eta": taxi_eta_min,
            "cost": 25,
            "pickup_time": 2,
            "drive_time": max(0, taxi_eta_min - 2),
            "traffic_level": "Moderate"
        }

        subway = {
            "eta": subway_eta,
            "cost": 3,
            "walk_to_station": subway_data["walk_minutes"],
            "wait_time": 0,
            "ride_time": subway_data["ride_minutes"],
            "transfers": subway_data["transfers"]
        }

        result = make_decision(subway, taxi, arrival_deadline, priority)

        weather = "clear"
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
            unsafe_allow_html=True
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
        st.write(f"Buffer: {result['buffer']} minutes")
                

        