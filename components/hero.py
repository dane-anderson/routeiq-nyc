from datetime import datetime, timedelta




def build_hero_card(decision_text: str, subway: dict, taxi: dict, result: dict) -> str:

    delay_status = subway.get("delay_status", "On time")

    is_subway = "Subway" in decision_text

    hero_bg = "#111827" if is_subway else "#FFC72C"
    hero_text = "#FFFFFF" if is_subway else "#111111"
    hero_muted = "#FACC15" if is_subway else "#4d3a00"
    chip_bg = "rgba(255,255,255,0.14)" if is_subway else "rgba(255,255,255,0.55)"
    leave_bg = "rgba(255,255,255,0.10)" if is_subway else "rgba(17,17,17,0.9)"

    leave_time = (
        datetime.now() + timedelta(minutes=max(result["leave_in"], 0))
    ).strftime("%I:%M %p").lstrip("0")

    if delay_status == "On time":
        delay_bg = "#e8f5e9"
        delay_color = "#2e7d32"
    elif delay_status == "Minor delays":
        delay_bg = "#fff8e1"
        delay_color = "#f57c00"
    else:
        delay_bg = "#ffebee"
        delay_color = "#c62828"
    return (
        f'<div class="hero" style="background:{hero_bg}; color:{hero_text};">'

            f'<div class="hero-top">'
                f'ROUTEIQ RECOMMENDS'
            f'</div>'

            f'<div class="hero-main">'
                f'{decision_text}'
            f'</div>'

            f'<div class="hero-chip" style="background:{chip_bg}; color:{hero_muted};">'
                f'Saves {abs(subway["eta"] - taxi["eta"])} minutes • More predictable'
            f'</div>'

            f'<div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:12px;">'

                f'<div style="background:{delay_bg}; '
                f'padding:6px 10px; border-radius:999px; '
                f'font-size:11px; font-weight:900; color:{delay_color};">'
                    f'🚇 {subway["delay_status"]}'
                f'</div>'

                f'<div style="background:rgba(255,255,255,0.45); '
                f'padding:6px 10px; border-radius:999px; '
                f'font-size:11px; font-weight:900; color:#4d3a00;">'
                    f'🚕 {taxi["traffic_level"]} traffic'
                f'</div>'

                f'<div style="background:rgba(255,255,255,0.45); '
                f'padding:6px 10px; border-radius:999px; '
                f'font-size:11px; font-weight:900; color:#4d3a00;">'
                    f'⏱ {result["buffer"]} min buffer'
                f'</div>'

            f'</div>'

            f'<div class="leave-box" style="background:{leave_bg};">'

                f'<div class="leave-label">'
                    f'Leave at'
                f'</div>'

                f'<div class="leave-number">'
                    f'{leave_time}'
                f'</div>'

                f'<div style="font-size:13px; color:#e5e7eb; margin-top:4px;">'
                    f'to arrive on time'
                f'</div>'

            f'</div>'

        f'</div>'
    )
