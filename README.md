# 🚕 RouteIQ-NYC

Built with Python, Streamlit, and OpenAI — deployed live on Render.

An AI-powered decision engine that compares subway vs taxi in NYC using structured route logic, confidence scoring, and a dynamic reasoning layer.

---

## 🚀 Live App  
https://routeiq-nyc.onrender.com/

---
## 🎬 Demo

<img src="routeiq-nyc.gif" width="800"/>---

## 🧠 What It Does  

RouteIQ is a Streamlit app powered by a decision engine and AI reasoning layer that helps users:

🚇 Compare subway vs car routes using live routing data (Google APIs)🚕 Evaluate time, cost, and traffic conditions  
🧠 Receive a clear recommendation based on priorities  
💬 Understand the decision through AI-generated reasoning  
⏱ See confidence based on arrival buffer (how early you’ll arrive)  

---

## 🧠 Overview  

RouteIQ is a decision-based AI application that combines structured logic with LLM-powered explanations.

Instead of relying only on AI, the system:

- Uses live routing data (Google Geocoding + Routes APIs)- Applies deterministic decision logic  
- Calculates arrival confidence using buffer time  
- Uses AI to translate decisions into natural, human-readable explanations  

This project demonstrates an **agent-style architecture**, where logic and AI work together to produce reliable, explainable outcomes.

🆕 Live Data Upgrade (Latest)

RouteIQ now uses real-world routing data instead of simulated inputs.

New capabilities:

📍 Users can enter real addresses (e.g. “Times Square, NYC” → “Wall Street, NYC”)
🗺 Addresses are converted to coordinates using the Google Geocoding API
🚗 Driving ETA is pulled live from the Google Routes API
🚇 Transit ETA is pulled live from the Google Routes API

This transforms RouteIQ from a simulated model into a real-time decision engine.
---

## ✨ Features  

### 🚇 Subway vs Taxi Comparison  
Compare routes based on:
- ETA  
- Cost  
- Transfers, walking, and wait time  

---

### 🧠 Decision Engine  
- Chooses best option based on:
  - fastest  
  - cheapest  
  - balanced  
- Uses weighted scoring for realistic tradeoffs  

---

### ⏱ Confidence + Buffer System  
- Calculates how early (or late) you’ll arrive  
- Translates that into:
  - You’ll get there comfortably  
  - You should get there on time  
  - It’s a close call  
  - Risky — you might be late  

---

🚦 Traffic Awareness (In Progress)
  -  Driving ETA reflects live routing data.
  -  Traffic labeling is currently estimated and will be upgraded to live traffic signals.

---

### 💬 AI Reasoning Layer  
- Explains decisions in natural language  
- Adapts to:
  - traffic conditions  
  - weather context  
  - user priority  
- Maintains a consistent, slightly NYC-style tone  

---

## 🛠 Tech Stack  

Python  
Streamlit  
OpenAI API  
Render (Cloud Deployment)  
Git + GitHub  

---

## 🚀 Deployment  

This app is fully deployed on Render and accessible here:

👉 https://routeiq-nyc.onrender.com/

Key deployment features:

- Python version control via `.python-version`  
- Environment variables for API security  
- Automated builds via GitHub integration  
- Live cloud hosting  

---

## 🌐 Deployment & Integration  

This application was built and deployed end-to-end, including:

- Local development using Streamlit  
- Integration with OpenAI for dynamic reasoning  
- Deployment to Render for public access  
- Environment configuration and version control  
- Debugging real-world deployment issues (Python versioning, dependencies)  

This project demonstrates the ability to build a **full AI-powered system**, not just a UI — from logic layer to deployment.

---

## 🛠️ Setup & Usage  

To run this project locally:

export OPENAI_API_KEY=your_key_here  
git clone https://github.com/dane-anderson/routeiq-nyc.git  
cd routeiq-nyc  
pip install -r requirements.txt  
streamlit run app.py  

---

⚠️ Current Limitations

While core routing is now live, some breakdown fields are still estimated:

- Walk time to station
- Wait time
- Ride time split
- Transfers
- Traffic level label
- Taxi pickup time

These will be upgraded to fully live data in upcoming iterations.

## 💡 Vision  

This project represents the foundation of a real-time AI travel assistant.

The goal is to evolve RouteIQ from a simulated decision engine into a **live, intelligent system** by integrating:

  - live transit breakdown (station, line, transfers)
  - MTA real-time service data (delays, alerts)
  - live traffic classification
  - live weather integration
  - rideshare pickup + pricing (Uber/Lyft APIs)

Ultimately, RouteIQ moves toward:

👉 **“Know when to leave. Know how to get there.”**
