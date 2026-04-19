def make_decision(subway, taxi, arrival_deadline, priority, weather):
    if priority == "fastest":
        recommendation = "subway" if subway["eta"] < taxi["eta"] else "taxi"

    elif priority == "cheapest":
        recommendation = "subway" if subway["cost"] < taxi["cost"] else "taxi"

    else:  
        walk_penalty = subway["walk_to_station"] * 3
        if weather == "rain":
            walk_penalty += subway["walk_to_station"] * 2

        subway_score = (
            subway["eta"]
            + (subway["cost"] * 2)
            + (subway["transfers"] * 3)
            + walk_penalty
    )
        taxi_score = taxi["eta"] + (taxi["cost"] * 2)

        if abs(subway["eta"] - taxi["eta"]) <= 3:
            recommendation = "subway" if subway["cost"] < taxi["cost"] else "taxi"
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


    if subway["delay_status"] == "Severe delays":
        explanation = "Subway delays are severe right now. Expect major disruptions — taking a taxi may save you time."

    elif subway["delay_status"] == "Minor delays":
        explanation = "There are some subway delays, but it's still a solid option depending on traffic."

    else:
        if weather == "rain":
            explanation = "Subway is running smoothly and it's raining — avoid getting soaked and take the train."
        elif weather == "snow":
            explanation = "Subway is running smoothly and snow can slow traffic — train is the safer bet."
        else:
            explanation = "Subway service is running smoothly. It's the fastest and most reliable option right now."

    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "buffer": buffer,
        "explanation": explanation,  
        "leave_in": leave_in
        
    }

    