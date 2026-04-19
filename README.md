



# 🚕 RouteIQ-NYC  
> 🚇🚕 **Take the right route — and know exactly when to leave.**

**RouteIQ is a real-time NYC decision engine that chooses between subway and taxi using live data, structured logic, and AI reasoning.**

Built with Python, Streamlit, Google Maps APIs, and OpenAI — deployed live on Render.

---

## 🚀 Live App  
👉 https://routeiq-nyc.onrender.com/



## 🎬 Demo

<img src="routeiq-nyc.gif" width="800"/>---
---
🧠 What It Does
RouteIQ helps users decide how to get somewhere in NYC — and when to leave.

It compares subway vs taxi using real routing data, then:

🚇 Calculates subway travel time (including multi-train routes)
🚕 Calculates taxi ETA using live routing data
🧠 Applies a decision engine based on user priorities
💬 Explains the decision using AI in a NYC-style voice
⏱ Shows confidence and leave timing
🪧 Visually displays subway routes using real MTA-style signage

RouteIQ now handles **multi-leg subway routes**, including transfers between trains, and presents them in a clean, visual format.

## ⚡ Why This Is Different

Most navigation apps tell you how to get somewhere.

RouteIQ tells you:

- 👉 **What decision to make** (subway vs taxi)
- 👉 **Why it’s the right choice** (AI reasoning layer)
- 👉 **When to leave** (real-time timing intelligence)

Instead of just routing, RouteIQ acts as a **decision engine** — combining live data, structured logic, and AI to guide real-world actions.

This project demonstrates:
- building systems, not just interfaces
- combining deterministic logic with LLM reasoning
- designing AI that supports decisions instead of replacing them
---

## 🧠 System Overview

RouteIQ combines deterministic logic + AI reasoning.

### 1. Data Layer
- Google Geocoding API → convert addresses into coordinates
- Google Routes API → fetch real-time ETAs for driving and transit

### 2. Decision Engine
Evaluates:
- time
- cost
- priority (`fastest`, `cheapest`, `balanced`)

Produces:
- recommendation
- arrival buffer
- confidence level
- leave timing

### 3. AI Reasoning Layer
- OpenAI API → turns structured trip decisions into natural-language explanations
- Adapts to:
  - weather
  - traffic
  - edge cases
- Uses a consistent NYC-style voice

---
✨ Features

🚇 **Subway vs Taxi Comparison**
- ETA comparison using live routing data  
- Cost comparison  
- Walk / ride / transfer breakdown  
- Supports multi-train routes with transfers

**📱 Smart Link Previews (NEW)**
Custom iMessage / social link previews

When shared, RouteIQ displays a clean, product-style preview card
instead of a raw URL

Try it:
https://routeiq-landing.onrender.com

🪧 **MTA-Style Route Visualization (NEW)**
- Displays subway routes using realistic NYC subway signage  
- Stacks multiple train legs vertically (e.g., E → C transfers)  
- Shows:
  - train line (color + symbol)  
  - direction / destination  
  - clean, readable route flow  

🧠 **Decision Engine**
- Weighted scoring system  
- Priority-based outcomes:
  - fastest  
  - cheapest  
  - balanced  

⏱ **Confidence + Leave Timing**
- Calculates arrival buffer  
- Converts that into:
  - “You’ll get there comfortably”  
  - “It’s a close call”  
  - “Risky — you might be late”  
- Shows:
  - Leave in X minutes  

💬 **AI Explanation Layer**
- Explains why the decision is correct  
- Context-aware based on weather and traffic  
- Conversational NYC tone  

🌧 **Weather Awareness**
- Adjusts reasoning based on conditions like rain  
- Impacts comfort and recommendation logic


---

## 🆕 Live Data Upgrade

RouteIQ now uses **real-world routing data** instead of simulated travel times.

- 📍 Input real addresses
- 🗺 Convert them to coordinates with the Geocoding API
- 🚗 Pull live driving ETA
- 🚇 Pull live transit ETA

This moves the project from simulation to a real-time decision system.

Now includes **multi-leg transit parsing**, enabling realistic subway routing with transfers.

---
⚠️ Current Limitations
Some breakdown fields are still estimated or simplified:

wait time
exact transfer timing
detailed ride segmentation
traffic level labeling
taxi pickup time

Transit routing depends on Google Routes API and may occasionally:
- favor longer walks over transfers
- miss optimal multi-line combinations

---

🔜 Next Up

📍 **Show transfer stations explicitly**
- e.g., “Transfer at 42 St–Port Authority”

🚦 **Add real MTA delay and alert context**

🚗 **Improve traffic classification**

🌦 **Expand weather integration**

🚕 **Add Uber/Lyft pricing and pickup estimates**

🧠 **Enhance decision engine**
- add risk tolerance  
- add time sensitivity  

---

## 🛠 Tech Stack

- Python
- Streamlit
- OpenAI API
- Google Maps APIs (Geocoding + Routes)
- Render
- Git + GitHub

---

## 🚀 Deployment

Fully deployed on Render:

👉 https://routeiq-nyc.onrender.com/

Includes:
- environment variable management
- GitHub auto-deploy
- production debugging and fixes

---

## 🛠️ Run Locally

```bash
export OPENAI_API_KEY=your_key_here
export GOOGLE_MAPS_API_KEY=your_key_here

git clone https://github.com/dane-anderson/routeiq-nyc.git
cd routeiq-nyc
pip install -r requirements.txt
streamlit run app.py
