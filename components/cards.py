LINE_COLORS = {
    "1": "#EE352E", "2": "#EE352E", "3": "#EE352E",
    "4": "#00933C", "5": "#00933C", "6": "#00933C",
    "7": "#B933AD",
    "A": "#0039A6", "C": "#0039A6", "E": "#0039A6",
    "B": "#FF6319", "D": "#FF6319", "F": "#FF6319", "M": "#FF6319",
    "N": "#FCCC0A", "Q": "#FCCC0A", "R": "#FCCC0A", "W": "#FCCC0A",
    "J": "#996633", "Z": "#996633",
    "G": "#6CBE45",
    "L": "#A7A9AC",
}

def build_train_boxes_html(subway_data: dict) -> str:
    transit_legs = subway_data.get("transit_legs", [])

    if not transit_legs:
        line_text = subway_data.get("line", "")
        if not line_text:
            return ""

        symbol = line_text.split(" ")[0]
        destination = subway_data.get("arrival", "Destination")
        subtitle = line_text.replace(f"{symbol} Train ", "").replace("(", "").replace(")", "")
        transit_legs = [{"line": line_text, "arrival": destination, "subtitle": subtitle}]

    boxes_html = '<div style="margin-top:14px; display:flex; flex-direction:column; gap:10px;">'

    for leg in transit_legs:
        line_text = leg.get("line", "")
        if not line_text:
            continue

        symbol = line_text.split(" ")[0]
        destination = leg.get("arrival", "Destination")
        subtitle = line_text.replace(f"{symbol} Train ", "").replace("(", "").replace(")", "")
        color = LINE_COLORS.get(symbol, "#111111")
        text_color = "#111111" if color == "#FCCC0A" else "#FFFFFF"

        boxes_html += (
            f'<div style="background:#111111; border-radius:15px; padding:13px 14px; '
            f'display:flex; align-items:center; gap:12px;">'
                f'<div style="width:36px; height:36px; border-radius:50%; background:{color}; '
                f'color:{text_color}; display:flex; align-items:center; justify-content:center; '
                f'font-size:16px; font-weight:900; flex-shrink:0;">{symbol}</div>'
                f'<div style="display:flex; flex-direction:column; gap:3px;">'
                    f'<div style="color:#FFFFFF; font-size:16px; font-weight:900; line-height:1.1;">{destination}</div>'
                    f'<div style="color:#D1D5DB; font-size:11px; font-weight:700; line-height:1.2;">{subtitle}</div>'
                f'</div>'
            f'</div>'
        )

    boxes_html += '</div>'
    return boxes_html