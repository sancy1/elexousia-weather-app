"""
FILE: backend/app/services/clothing_advice.py
Rule-based clothing recommendations shared by the /weather/wear endpoints
and the agent's get_clothing_advice tool.
"""

from typing import Any


def generate_clothing_advice(
    temp_c: float,
    condition: str,
    rain_chance: int,
    uv_index: int,
    occasion: str = "general",
) -> dict[str, Any]:
    """
    Generate clothing recommendations based on weather conditions.

    Args:
        temp_c: temperature in Celsius
        condition: human-readable condition text (e.g. "Partly cloudy")
        rain_chance: precipitation probability 0-100
        uv_index: UV index
        occasion: "general" | "work" | "formal" | "outdoor"

    Returns:
        dict with emoji, summary, tagline, items, tip
    """
    items = []
    emoji = "☀️"
    summary = "Light layers"
    tagline = "Comfortable weather"

    # Temperature-based recommendations
    if temp_c < 5:
        items.append(
            {"icon": "🧥", "name": "Heavy winter coat", "note": "Insulated or down jacket"}
        )
        items.append(
            {"icon": "🧣", "name": "Scarf and gloves", "note": "Essential for cold protection"}
        )
        items.append({"icon": "👢", "name": "Insulated boots", "note": "Waterproof recommended"})
        emoji = "❄️"
        summary = "Winter layers"
        tagline = "Stay warm out there"
    elif temp_c < 15:
        items.append(
            {"icon": "🧥", "name": "Medium-weight jacket", "note": "Fleece or light parka"}
        )
        items.append({"icon": "👕", "name": "Long-sleeve shirt", "note": "Layer for warmth"})
        emoji = "🍂"
        summary = "Cool weather gear"
        tagline = "A light jacket does the trick"
    elif temp_c < 25:
        items.append({"icon": "👕", "name": "Light layers", "note": "T-shirt with light cardigan"})
        items.append(
            {"icon": "👖", "name": "Pants or jeans", "note": "Comfortable for mild weather"}
        )
        emoji = "🌤️"
        summary = "Comfortable layers"
        tagline = "Perfect weather"
    else:
        items.append(
            {
                "icon": "👕",
                "name": "Light, breathable clothing",
                "note": "Cotton or moisture-wicking fabrics",
            }
        )
        items.append({"icon": "🧢", "name": "Hat and sunglasses", "note": "Sun protection"})
        emoji = "☀️"
        summary = "Summer essentials"
        tagline = "Stay cool and protected"

    # Condition-based additions
    if rain_chance > 50 or "rain" in condition.lower() or "drizzle" in condition.lower():
        items.insert(0, {"icon": "☂️", "name": "Umbrella", "note": "Compact or waterproof"})
        items.insert(
            1, {"icon": "🧥", "name": "Waterproof jacket", "note": "Rain shell or trench coat"}
        )
        items.append({"icon": "👟", "name": "Waterproof shoes", "note": "Avoid suede and canvas"})
        emoji = "🌧️"
        summary = "Rain-ready layers"
        tagline = "Stay dry, stay sharp"
    elif "snow" in condition.lower():
        items.insert(
            0, {"icon": "🧥", "name": "Waterproof winter coat", "note": "Insulated and windproof"}
        )
        items.insert(
            1, {"icon": "👢", "name": "Snow boots", "note": "Insulated with good traction"}
        )
        emoji = "❄️"
        summary = "Winter storm gear"
        tagline = "Bundle up tight"

    # UV-based additions
    if uv_index >= 8:
        if not any(item["name"] == "Hat and sunglasses" for item in items):
            items.append(
                {"icon": "🧢", "name": "Hat and sunglasses", "note": "UV protection essential"}
            )
        items.append(
            {"icon": "🧴", "name": "SPF 50+ sunscreen", "note": "Apply generously and reapply"}
        )

    # Occasion adjustments
    if occasion == "formal":
        items = [item for item in items if "T-shirt" not in item["name"]]
        items.append(
            {"icon": "👔", "name": "Formal attire", "note": "Consider dress code requirements"}
        )
        summary = "Formal weather-ready"
    elif occasion == "work":
        items.append(
            {"icon": "💼", "name": "Work-appropriate layers", "note": "Business casual options"}
        )

    # Generate tip
    if rain_chance > 60:
        tip = "Showers expected on and off — keep an umbrella within reach all day."
    elif temp_c > 30:
        tip = "Hot conditions — stay hydrated and seek shade when possible."
    elif temp_c < 5:
        tip = "Very cold — limit exposed skin and dress in layers."
    elif uv_index >= 8:
        tip = "Very high UV — apply sunscreen every 2 hours if outdoors."
    else:
        tip = "Pleasant conditions — enjoy your day!"

    return {"emoji": emoji, "summary": summary, "tagline": tagline, "items": items, "tip": tip}
