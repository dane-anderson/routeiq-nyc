import streamlit as st
from data_simulator import get_subway_option, get_taxi_option
from decision_engine import make_decision
from ai_voice import generate_reasoning


st.set_page_config(page_title="RouteIQ-NYC", page_icon="🚕", layout="wide")

st.markdown("""
<style>
/* Background */
body {
    background-color: #FFFFFF;
}

/* Title */
h1 {
    color: #111111;
    font-weight: 800;
}

/* Subtitle */
h2, h3 {
    color: #333333;
}

/* Buttons */
.stButton > button {
    background-color: #FFC72C;
    color: black;
    font-weight: 600;
    border-radius: 8px;
    padding: 0.6em 1.2em;
}

/* Input boxes */
.stTextInput input, .stNumberInput input {
    border-radius: 8px;
}

/* Page spacing */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Premium cards */
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

    origin = st.text_input("Origin", placeholder="Upper East Side")
    destination = st.text_input("Destination", placeholder="SoHo")

    arrival_deadline = st.number_input(
        "Must arrive within how many minutes?",
        min_value=1,
        value=45
    )

    priority = st.selectbox("Priority", ["fastest", "cheapest", "balanced"])

    run = st.button("Make Decision")

with col2:
    if run:
        subway = get_subway_option(origin, destination)
        taxi = get_taxi_option(origin, destination)

        result = make_decision(subway, taxi, arrival_deadline, priority)

        weather = "clear"

        reasoning = generate_reasoning(
            result["recommendation"],
            subway,
            taxi,
            priority,
            weather
        )

        if result["recommendation"] == "subway":
            decision_icon = "🚇"
            decision_text = "Take the Subway"
            bg_color = "#111111"
            text_color = "white"
        else:
            decision_icon = "🚕"
            decision_text = "Take the Taxi"
            bg_color = "#FFC72C"
            text_color = "black"

        st.markdown(
            f"""
            <div style="
                background-color: {bg_color};
                color: {text_color};
                padding: 20px;
                border-radius: 14px;
                text-align: center;
                font-size: 26px;
                font-weight: 600;
                margin-bottom: 15px;
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
        st.info(reasoning)

        st.markdown("### Confidence")
        st.write(result["confidence"].title())
        st.write(f"Buffer: {result['buffer']} minutes")