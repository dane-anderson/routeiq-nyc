def build_hero_card(decision_text: str, subway: dict, taxi: dict, result: dict) -> str:
    return (
        f'<div class="hero">'

            f'<div class="hero-top">'
                f'ROUTEIQ RECOMMENDS'
            f'</div>'

            f'<div class="hero-main">'
                f'{decision_text}'
            f'</div>'

            f'<div class="hero-chip">'
                f'Saves {abs(subway["eta"] - taxi["eta"])} minutes • More predictable'
            f'</div>'

            f'<div class="leave-box">'

                f'<div class="leave-label">'
                    f'Leave in'
                f'</div>'

                f'<div class="leave-number">'
                    f'{max(result["leave_in"], 0)} min'
                f'</div>'

                f'<div style="font-size:13px; color:#e5e7eb; margin-top:4px;">'
                    f'to arrive on time'
                f'</div>'

            f'</div>'

        f'</div>'
    )