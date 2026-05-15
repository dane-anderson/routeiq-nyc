def get_confidence_score(confidence_text: str) -> int:
    text = (confidence_text or "").lower()

    if "comfortably" in text:
        return 72
    if "good chance" in text or "likely" in text:
        return 64
    if "tight" in text or "close" in text:
        return 52
    if "risk" in text or "unlikely" in text:
        return 38
    return 60