"""Translate Vosk transcripts into supported light actions."""


def check_light_command(text: str) -> str:
    """Return ``ON``, ``OFF``, or ``UNKNOWN`` for a spoken light command."""
    normalized_text = text.lower().strip()
    on_phrases = (
        "lights on",
        "light on",
        "turn on",
        "turn on light",
        "turn on lights",
        "turn the light on",
        "turn the lights on",
        "switch on",
    )
    off_phrases = (
        "lights off",
        "light off",
        "turn off",
        "turn off light",
        "turn off lights",
        "turn the light off",
        "turn the lights off",
        "switch off",
        "the north",
    )

    if any(phrase in normalized_text for phrase in on_phrases):
        return "ON"
    if any(phrase in normalized_text for phrase in off_phrases):
        return "OFF"

    words = set(normalized_text.split())
    if "on" in words and {"turn", "switch", "light", "lights"} & words:
        return "ON"
    if "off" in words and {"turn", "switch", "light", "lights"} & words:
        return "OFF"
    return "UNKNOWN"
