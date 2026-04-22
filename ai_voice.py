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

def looks_broken(text):
    if re.search(r"\d+[a-zA-Z]+", text):
        return True
    if re.search(r"[a-zA-Z]{15,}", text):
        return True
    
    return False


def generate_reasoning(recommendation, subway, taxi, priority, weather):
    try:
        ai_text = generate_ai_reasoning(recommendation, subway, taxi, priority, weather)
        if ai_text:
            return ai_text
    except Exception:
        pass

    fallback_text = generate_fallback_reasoning(recommendation, subway, taxi, priority, weather)
    return fallback_text if fallback_text else "Take the recommended option based on time, cost, and conditions."


def generate_ai_reasoning(recommendation, subway, taxi, priority, weather):
    traffic = taxi.get("traffic_level", "Normal")
    decision = recommendation
    delay_status = subway.get("delay_status", "On time")

    if traffic == "Light":
        traffic_line = "Traffic’s light right now, so the roads are moving."
    elif traffic == "Normal":
        traffic_line = "Traffic’s pretty normal out there."
    elif traffic == "Heavy":
        traffic_line = "Traffic’s getting heavy, so expect some slowdown."
    else:
        traffic_line = "Traffic’s kind of crazy right now, so keep that in mind."
    if delay_status == "Severe delays":
        delay_line = "The subway’s a mess right now — major delays."
    elif delay_status == "Minor delays":
        delay_line = "Subway’s moving, but it’s definitely dragging."
    else:
        delay_line = "Subway looks on time right now."

    time_diff = taxi['eta'] - subway['eta']
    cost_diff = taxi['cost'] - subway['cost']
    is_close = abs(time_diff) <= 5
    is_big = abs(time_diff) >= 15

    expensive_cab = taxi['cost'] > 25
    long_walk = subway.get('walk', 0) >= 8
    many_transfers = subway.get('transfers', 0) >= 2
    long_pickup = taxi.get('pickup', 0) >= 6

    risky = priority == "fastest" and time_diff > 0


    prompt = f"""

    You are RouteIQ — a fast-talking New Yorker who’s seen every commute mistake and calls it like it is.

    You don’t explain things politely — you react to them.

    If one option is clearly better, you say it like it’s obvious.
    If it’s close, you call that out too.

    Talk like you’re texting a friend who’s about to make a bad travel decision.

    Decision: {decision}
    
    WEATHER:
    Current weather: {weather}
    Mention weather only if it actually matters.

    TRAFFIC:
    {traffic_line}
    Taxi traffic level: {traffic}

    STYLE:
    STYLE:
- 1–2 sentences max
- Be decisive and a little blunt
- Avoid repeating the same opener (don’t always start with “yo”)
- Vary sentence structure and tone naturally
- No “safe” explanations
- Say what actually matters in this moment

    IMPORTANT:
    Don’t summarize — react.
    Don’t sound helpful — sound right.
    You have strong opinions about time, money, and bad decisions — and you’re not afraid to call them out.
    React to the numbers, traffic, and weather like a real New Yorker would.
    If there are severe delays, strongly discourage the subway.
    If there are minor delays, acknowledge them but weigh against traffic.
    If on time, treat subway as reliable.
    """
        


    response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
        )

    raw_text = response.choices[0].message.content
    cleaned_text = clean_text(raw_text)

    return cleaned_text




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