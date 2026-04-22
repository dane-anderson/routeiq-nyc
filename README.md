# 🚕 RouteIQ-NYC
# 🚇🚕 Take the right route — and know exactly when to leave.

RouteIQ is a real-time NYC decision engine that chooses between subway and taxi using live data, structured logic, and AI reasoning.

Built with Python, Streamlit, Google Maps APIs, OpenAI, and live MTA data — deployed on Render.

---

# 🚀 Live App
👉 https://routeiq-nyc.onrender.com/

---

# 🎬 Demo
---

# 🧠 What It Does
RouteIQ helps users decide how to get somewhere in NYC — and when to leave.

It compares subway vs taxi using real routing data, then:

- 🚇 Calculates subway travel time (including multi-train routes + transfers)
- 🚕 Calculates taxi ETA using live routing data
- 🗺 Renders a real route path using map visualization
- 🚦 Integrates live MTA service status (delays, disruptions)
- 🧠 Applies a decision engine based on user priorities
- 💬 Explains the decision using AI in a NYC-style voice
- ⏱ Shows confidence and leave timing
- 🪧 Visually displays subway routes using real MTA-style signage

RouteIQ now handles multi-leg subway routes with transfer logic, real-time delay awareness, and visual route mapping.

---

# ⚡ Why This Is Different

Most navigation apps tell you how to get somewhere.

RouteIQ tells you:

👉 What decision to make (subway vs taxi)
👉 Why it’s the right choice (AI reasoning layer)
👉 When to leave (real-time timing intelligence)

Instead of just routing, RouteIQ acts as a decision engine — combining live data, structured logic, and AI to guide real-world actions.

This project demonstrates:

- building systems, not just interfaces
- combining deterministic logic with LLM reasoning
- designing AI that supports decisions instead of replacing them

---

# 🧠 System Overview

RouteIQ combines deterministic logic + real-time data + AI reasoning.

---

## 1. Data Layer
- Google Geocoding API → convert addresses into coordinates
- Google Routes API → fetch real-time ETAs for driving and transit
- MTA Service Status API → live subway delays and alerts

---

## 2. Decision Engine

Evaluates:

- time
- cost
- priority (fastest, cheapest, balanced)
- service reliability (MTA status integration)

Produces:

- recommendation
- arrival buffer
- confidence level
- leave timing

---

## 3. AI Reasoning Layer

OpenAI API → turns structured trip decisions into natural-language explanations

Adapts to:

- weather
- traffic
- subway delays
- edge cases

Uses a consistent NYC-style voice

---

# ✨ Features

## 🚇 Subway vs Taxi Comparison

- ETA comparison using live routing data
- Cost comparison
- Walk / ride / transfer breakdown
- Supports multi-train routes with transfers

---

## 🗺 Route Map Visualization (NEW)

- Displays route paths directly in the UI
- Uses real polyline data from Google Routes API
- Shows spatial flow of trips (not just numbers)
- Enhances decision clarity and realism

---

## 🚦 Live MTA Status Integration (NEW)

- Pulls real-time subway service status
- Detects:
  - delays
  - service changes
  - disruptions
- Feeds directly into:
  - decision engine
  - AI explanation layer

---

## 📱 Smart Link Previews (NEW)

Custom iMessage / social link previews

When shared, RouteIQ displays a clean, product-style preview card instead of a raw URL

👉 https://routeiq-landing.onrender.com

---

## 🪧 MTA-Style Route Visualization

Displays subway routes using realistic NYC subway signage

- Stacks multiple train legs vertically (e.g., E → C transfers)
- Shows:
  - train line (color + symbol)
  - direction / destination
  - clean, readable route flow

---

## 🧠 Decision Engine

- Weighted scoring system
- Priority-based outcomes:
  - fastest
  - cheapest
  - balanced
- Now incorporates real-world reliability signals (MTA delays)

---

## ⏱ Confidence + Leave Timing

- Calculates arrival buffer
- Converts that into:
  - “You’ll get there comfortably”
  - “It’s a close call”
  - “Risky — you might be late”
- Shows:
  - Leave in X minutes

---

## 💬 AI Explanation Layer

- Explains why the decision is correct
- Context-aware based on:
  - weather
  - traffic
  - subway delays
- Conversational NYC tone

---

## 🌧 Weather Awareness

- Adjusts reasoning based on conditions like rain
- Impacts comfort and recommendation logic

---

# 🆕 Live Data Upgrade

RouteIQ now operates as a true real-time decision system:

- 📍 Input real addresses
- 🗺 Convert them to coordinates
- 🚗 Pull live driving ETA
- 🚇 Pull live transit ETA
- 🚦 Incorporate live MTA service conditions
- 🗺 Render actual route paths

This moves the project from simulation → real-world decision intelligence

---

# ⚠️ Current Limitations

Some breakdown fields are still estimated or simplified:

- wait time
- exact transfer timing
- detailed ride segmentation
- traffic level labeling
- taxi pickup time

Transit routing depends on Google Routes API and may occasionally:

- favor longer walks over transfers
- miss optimal multi-line combinations

---

# 🔜 Next Up

- 📍 Show transfer stations explicitly
  - e.g., “Transfer at 42 St–Port Authority”

- 🚗 Improve traffic classification

- 🌦 Expand weather integration

- 🚕 Add Uber/Lyft pricing + pickup estimates

- 🧠 Enhance decision engine
  - risk tolerance
  - time sensitivity

- 🗺 Improve map rendering
  - subway vs taxi visual comparison
  - multi-route overlays

---

# 🛠 Tech Stack

- Python
- Streamlit
- OpenAI API
- Google Maps APIs (Geocoding + Routes)
- MTA Service Status API
- Render
- Git + GitHub

---

# 🚀 Deployment

Fully deployed on Render:

👉 https://routeiq-nyc.onrender.com/

Includes:

- environment variable management
- GitHub auto-deploy
- production debugging and fixes

---

# 🛠️ Run Locally

export OPENAI_API_KEY=your_key_here
export GOOGLE_MAPS_API_KEY=your_key_here

git clone https://github.com/dane-anderson/routeiq-nyc.git
cd routeiq-nyc
pip install -r requirements.txt
streamlit run app.py
