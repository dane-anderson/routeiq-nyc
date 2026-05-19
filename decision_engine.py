def make_decision(subway, taxi, arrival_deadline, priority, weather):
    subway_delay_status = subway.get("delay_status", "On time")

    delay_penalty = 0
    if subway_delay_status == "Severe delays":
        delay_penalty = 25
    elif subway_delay_status == "Minor delays":
        delay_penalty = 8

    walk_penalty = subway["walk_to_station"] * 3
    if weather == "rain":
        walk_penalty += subway["walk_to_station"] * 2
    elif weather == "snow":
        walk_penalty += subway["walk_to_station"] * 2

    transfer_penalty = subway["transfers"] * 5

    subway_score = (
        subway["eta"]
        + (subway["cost"] * 2)
        + transfer_penalty
        + walk_penalty
        + delay_penalty
    )

    taxi_score = taxi["eta"] + (taxi["cost"] * 2)

    if priority == "fastest":
        recommendation = "subway" if (subway["eta"] + delay_penalty) < taxi["eta"] else "taxi"

    elif priority == "cheapest":
        if subway_delay_status == "Severe delays":
            recommendation = "taxi" if taxi["eta"] <= subway["eta"] + 15 else "subway"
        else:
            recommendation = "subway" if subway["cost"] < taxi["cost"] else "taxi"

    else:
        if abs(subway["eta"] - taxi["eta"]) <= 3:
            recommendation = "subway" if subway["cost"] < taxi["cost"] and subway_delay_status != "Severe delays" else "taxi"
        else:
            recommendation = "subway" if subway_score < taxi_score else "taxi"

    chosen_eta = subway["eta"] if recommendation == "subway" else taxi["eta"]
    buffer = arrival_deadline - chosen_eta
    leave_in = max(buffer, 0)

    if buffer >= 10:
        confidence = "You’ll get there comfortably"
    elif buffer >= 5:
        confidence = "You should get there on time"
    elif buffer >= 0:
        confidence = "It’s a close call"
    else:
        confidence = "Risky — you might be late"

    if subway_delay_status == "Severe delays":
        explanation = "Subway delays are severe right now, so RouteIQ is penalizing the train heavily."
    elif subway_delay_status == "Minor delays":
        explanation = "Subway has minor delays, so RouteIQ is adding some risk to the train option."
    else:
        explanation = "Subway service looks normal, so RouteIQ is treating the train as reliable."

    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "buffer": buffer,
        "explanation": explanation,
        "leave_in": leave_in,
        "subway_score": subway_score,
        "taxi_score": taxi_score,
        "delay_penalty": delay_penalty,
        "walk_penalty": walk_penalty,
        "transfer_penalty": transfer_penalty,
    }