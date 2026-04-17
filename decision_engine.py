def make_decision(subway, taxi, arrival_deadline, priority):
    if priority == "fastest":
        recommendation = "subway" if subway["eta"] < taxi["eta"] else "taxi"

    elif priority == "cheapest":
        recommendation = "subway" if subway["cost"] < taxi["cost"] else "taxi"

    else:  # balanced
        subway_score = subway["eta"] + (subway["cost"] * 2)
        taxi_score = taxi["eta"] + (taxi["cost"] * 2)
        recommendation = "subway" if subway_score < taxi_score else "taxi"

    chosen_eta = subway["eta"] if recommendation == "subway" else taxi["eta"]
    buffer = arrival_deadline - chosen_eta

    if buffer >= 10:
        confidence = "You’ll get there comfortably"
    elif buffer >= 5:
        confidence = "You should get there on time"
    elif buffer >= 0:
        confidence = "It’s a close call"
    else:
        confidence = "Risky — you might be late"

    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "buffer": buffer
    }