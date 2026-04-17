import random
import re
from openai import OpenAI

client = OpenAI()

def clean_text(text):
    text = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", text)
    text = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", text)
    text = re.sub(r"([.,!$])([a-zA-Z])", r"\1 \2", text)
    text = text.replace("—", " — ")
    text = text.replace("’", "'")
    text = text.replace("**", "").replace("_", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def generate_reasoning(recommendation, subway, taxi, priority, weather):
    try:
        return generate_ai_reasoning(recommendation, subway, taxi, priority, weather)
    except Exception:
        return generate_fallback_reasoning(recommendation, subway, taxi, priority, weather)


def generate_ai_reasoning(recommendation, subway, taxi, priority, weather):
    traffic = taxi.get("traffic_level", "Normal")

    if traffic == "Light":
        traffic_line = "Traffic’s light right now, so the roads are moving."
    elif traffic == "Normal":
        traffic_line = "Traffic’s pretty normal out there."
    elif traffic == "Heavy":
        traffic_line = "Traffic’s getting heavy, so expect some slowdown."
    else:
        traffic_line = "Traffic’s kind of crazy right now, so keep that in mind."

    prompt = f"""

You are a sharp, slightly witty New Yorker giving quick travel advice.

Rules:
- Keep it to 2 sentences max
- Always include dollar signs ($) when mentioning prices
- Always include the word "minutes" for time
- Use the exact numbers provided
- Do not drop or shorten prices
- Do not write plain numbers for money
- Do not invent or change ETA or price values
- Use normal spacing between all words and numbers
- Never combine words together
- Leave a normal space after punctuation
- Write clean, readable sentences only
- Do not use markdown, italics, or special formatting

Tone:
- confident
- concise
- lightly funny
- natural, not cheesy
- subtle NYC vibe

Weather context:
- Current weather: {weather}
- If rainy, you may mention an umbrella or avoiding getting soaked
- If sunny or hot, you may mention heat, walking, or sunscreen naturally
- Only mention weather if it feels relevant

Traffic context:
- {traffic_line}
- Taxi traffic level: {traffic}

Trip data:
- Recommendation: {recommendation}
- Subway ETA: {subway['eta']} minutes
- Taxi ETA: {taxi['eta']} minutes
- Subway cost: ${subway['cost']:.2f}
- Taxi cost: ${taxi['cost']:.2f}
- Priority: {priority}

Write a natural explanation for the recommendation.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.choices[0].message.content
    return clean_text(raw_text)


def generate_fallback_reasoning(recommendation, subway, taxi, priority, weather):
    weather_tips = {
        "rainy": " Bring an umbrella.",
        "heavy rain": " Honestly, getting drenched for this commute is not the move.",
        "sunny": " Nice day out, at least.",
        "hot": " It’s hot out, so that extra walking may feel longer than it sounds.",
        "cold": " It’s cold out, so standing around outside won’t be fun.",
        "clear": "",
    }

    traffic_tips = {
        "Light": " Roads are moving pretty well.",
        "Normal": " Traffic’s fairly normal right now.",
        "Heavy": " Traffic’s getting heavy out there.",
        "Crazy": " Traffic’s kind of wild right now.",
    }

    weather_note = weather_tips.get(weather.lower(), "")
    traffic_level = taxi.get("traffic_level", "Normal")
    traffic_note = traffic_tips.get(traffic_level, "")

    if recommendation == "taxi":
        faster_by = subway["eta"] - taxi["eta"]

        fast_taxi_lines = [
            f"Take the cab. {taxi['eta']} minutes vs {subway['eta']} minutes — that’s an easy call. {traffic_note}{weather_note}",
            f"Taxi wins. You’re saving about {faster_by} minutes today. {traffic_note}{weather_note}",
            f"Grab a cab. The train’s slower right now — not even close. {traffic_note}{weather_note}",
        ]

        cheap_loss_taxi_lines = [
            f"Yeah, it’s about ${taxi['cost']:.2f}, but you’re buying back time. {traffic_note}{weather_note}",
            f"Not cheap at ${taxi['cost']:.2f}, but today speed matters more. {traffic_note}{weather_note}",
            f"It costs more, but the time savings make it worth it this run. {traffic_note}{weather_note}",
        ]

        balanced_taxi_lines = [
            f"Take the cab. Faster, cleaner, no waiting around. {traffic_note}{weather_note}",
            f"Taxi’s the better move — less hassle and quicker overall. {traffic_note}{weather_note}",
            f"Cab it. Streets are actually working in your favor for once. {traffic_note}{weather_note}",
        ]

        if priority == "fastest":
            return random.choice(fast_taxi_lines + cheap_loss_taxi_lines)
        elif priority == "balanced":
            return random.choice(balanced_taxi_lines + fast_taxi_lines)
        else:
            return random.choice(cheap_loss_taxi_lines + balanced_taxi_lines)

    else:
        cheaper_by = taxi["cost"] - subway["cost"]
        faster_by = taxi["eta"] - subway["eta"]

        cheap_subway_lines = [
            f"Take the subway. ${subway['cost']:.2f} vs ${taxi['cost']:.2f} — not even close. {traffic_note}{weather_note}",
            f"Subway wins on price. You’re saving about ${cheaper_by:.2f}. {traffic_note}{weather_note}",
            f"Go underground. Way cheaper than the cab today. {traffic_note}{weather_note}",
        ]

        fast_subway_lines = [
            f"Take the subway. {subway['eta']} minutes beats {taxi['eta']} minutes right now. {traffic_note}{weather_note}",
            f"The train is faster today — about {faster_by} minutes quicker. {traffic_note}{weather_note}",
            f"Subway wins. The cab’s just slower this time. {traffic_note}{weather_note}",
        ]

        balanced_subway_lines = [
            f"Take the subway. Cheap, reliable, and solid timing. {traffic_note}{weather_note}",
            f"Subway’s the smarter play — no surge, no guessing. {traffic_note}{weather_note}",
            f"Go with the train. Keeps things simple and affordable. {traffic_note}{weather_note}",
        ]

        if priority == "cheapest":
            return random.choice(cheap_subway_lines + balanced_subway_lines)
        elif priority == "fastest":
            return random.choice(fast_subway_lines + balanced_subway_lines)
        else:
            return random.choice(balanced_subway_lines + cheap_subway_lines)