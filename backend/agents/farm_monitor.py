import anthropic
import json
import random
import math
from datetime import datetime, timedelta
from typing import AsyncIterator

MONITOR_SYSTEM_PROMPT = """You are an expert farm monitoring AI with deep expertise in precision agriculture, crop science, and farm management.
You analyze real-time farm sensor data, weather conditions, and crop status to provide actionable insights.

When monitoring a farm you:
- Identify early warning signs of crop stress, disease, or pest pressure
- Correlate sensor readings with optimal growing conditions for specific crops
- Provide immediate action recommendations
- Track trends over time to predict future issues
- Celebrate wins and good farming practices
- Give confidence scores for your assessments

Be direct, specific, and prioritize urgent issues. Use simple language farmers understand.
Always end recommendations with a clear next-action list."""


def generate_sensor_data(farm_profile: dict) -> dict:
    """Generate realistic sensor readings based on farm profile and current date."""
    now = datetime.now()
    hour = now.hour
    day_of_year = now.timetuple().tm_yday

    # Temperature varies by time of day and season
    base_temp = 22 + 8 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    temp_variation = 6 * math.sin(2 * math.pi * (hour - 6) / 24)
    temperature = round(base_temp + temp_variation + random.uniform(-2, 2), 1)

    # Humidity inversely related to temperature
    humidity = round(max(30, min(95, 75 - (temperature - 20) * 1.5 + random.uniform(-5, 5))), 1)

    # Soil moisture (simulate irrigation cycles)
    soil_moisture = round(random.uniform(45, 75), 1)

    # Soil pH
    soil_ph = round(random.uniform(5.8, 7.2), 2)

    # Light intensity (lux) - peaks at noon
    light_lux = max(0, int(80000 * math.sin(math.pi * (hour - 6) / 12) * random.uniform(0.7, 1.0))) if 6 <= hour <= 18 else 0

    # Nutrient levels (ppm)
    nitrogen = round(random.uniform(150, 280), 1)
    phosphorus = round(random.uniform(30, 80), 1)
    potassium = round(random.uniform(120, 250), 1)

    # Wind speed (m/s)
    wind_speed = round(random.uniform(0.5, 8.0), 1)

    # Rainfall last 24h (mm)
    rainfall_24h = round(random.uniform(0, 15), 1) if random.random() > 0.6 else 0

    # CO2 levels (ppm) - slightly elevated in crop canopy
    co2_ppm = round(random.uniform(390, 450), 0)

    # Plant health index (0-100, simulated)
    health_index = round(random.uniform(65, 95), 1)

    # Pest pressure (0-10)
    pest_pressure = round(random.uniform(0, 3), 1)

    return {
        "timestamp": now.isoformat(),
        "temperature_c": temperature,
        "humidity_percent": humidity,
        "soil_moisture_percent": soil_moisture,
        "soil_ph": soil_ph,
        "light_lux": light_lux,
        "nitrogen_ppm": nitrogen,
        "phosphorus_ppm": phosphorus,
        "potassium_ppm": potassium,
        "wind_speed_ms": wind_speed,
        "rainfall_24h_mm": rainfall_24h,
        "co2_ppm": co2_ppm,
        "plant_health_index": health_index,
        "pest_pressure_index": pest_pressure,
        "battery_percent": round(random.uniform(72, 99), 0),
        "signal_strength": random.choice(["Excellent", "Good", "Good", "Fair"])
    }


def generate_historical_data(days: int = 7) -> list:
    """Generate historical sensor data for trend analysis."""
    history = []
    now = datetime.now()

    for i in range(days * 24):  # Hourly data
        timestamp = now - timedelta(hours=(days * 24 - i))
        hour = timestamp.hour
        day_of_year = timestamp.timetuple().tm_yday

        base_temp = 22 + 8 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
        temp_variation = 6 * math.sin(2 * math.pi * (hour - 6) / 24)

        history.append({
            "timestamp": timestamp.isoformat(),
            "temperature_c": round(base_temp + temp_variation + random.uniform(-1.5, 1.5), 1),
            "humidity_percent": round(random.uniform(40, 85), 1),
            "soil_moisture_percent": round(random.uniform(40, 80), 1),
            "plant_health_index": round(random.uniform(60, 98), 1)
        })

    # Return only daily aggregates for the last 7 days
    daily = []
    for d in range(days):
        day_data = history[d * 24:(d + 1) * 24]
        daily.append({
            "date": (now - timedelta(days=days - 1 - d)).strftime("%Y-%m-%d"),
            "avg_temp": round(sum(r["temperature_c"] for r in day_data) / len(day_data), 1),
            "avg_humidity": round(sum(r["humidity_percent"] for r in day_data) / len(day_data), 1),
            "avg_soil_moisture": round(sum(r["soil_moisture_percent"] for r in day_data) / len(day_data), 1),
            "avg_health": round(sum(r["plant_health_index"] for r in day_data) / len(day_data), 1)
        })

    return daily


async def analyze_farm_status(
    client: anthropic.Anthropic,
    farm_profile: dict,
    sensor_data: dict,
    historical: list,
    user_observations: str = ""
) -> AsyncIterator[str]:
    """Stream AI analysis of current farm status."""

    context = f"""
**Farm Profile:**
- Farm Name: {farm_profile.get('name', 'My Farm')}
- Crops Growing: {farm_profile.get('crops', 'Various')}
- Farm Size: {farm_profile.get('area', 'Unknown')} hectares
- Growing Stage: {farm_profile.get('growth_stage', 'Vegetative')}
- Days Since Planting: {farm_profile.get('days_planted', 'Unknown')}

**Current Sensor Readings (Live):**
- Temperature: {sensor_data['temperature_c']}°C
- Humidity: {sensor_data['humidity_percent']}%
- Soil Moisture: {sensor_data['soil_moisture_percent']}%
- Soil pH: {sensor_data['soil_ph']}
- Light Intensity: {sensor_data['light_lux']:,} lux
- Nitrogen (N): {sensor_data['nitrogen_ppm']} ppm
- Phosphorus (P): {sensor_data['phosphorus_ppm']} ppm
- Potassium (K): {sensor_data['potassium_ppm']} ppm
- Wind Speed: {sensor_data['wind_speed_ms']} m/s
- Rainfall (24h): {sensor_data['rainfall_24h_mm']} mm
- CO2 Level: {sensor_data['co2_ppm']} ppm
- Plant Health Index: {sensor_data['plant_health_index']}/100
- Pest Pressure: {sensor_data['pest_pressure_index']}/10

**7-Day Trend (Daily Averages):**
{json.dumps(historical, indent=2)}

**Farmer's Observations:**
{user_observations if user_observations else 'No additional observations provided.'}

Please provide:
1. Overall farm health assessment with score (0-100)
2. Critical alerts (if any)
3. Key findings from sensor data
4. Trend analysis
5. Immediate action items (prioritized)
6. What's going well on this farm
7. 3-day outlook
"""

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=[{"type": "text", "text": MONITOR_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": context}]
    ) as stream:
        for text in stream.text_stream:
            yield text


async def chat_about_farm(
    client: anthropic.Anthropic,
    farm_profile: dict,
    sensor_data: dict,
    conversation_history: list,
    user_message: str
) -> AsyncIterator[str]:
    """Stream chat response about the farm."""

    system = f"""You are a knowledgeable farm advisor monitoring {farm_profile.get('name', 'this farm')} in real-time.

Current farm stats:
- Crops: {farm_profile.get('crops', 'Various')}
- Temperature: {sensor_data['temperature_c']}°C
- Humidity: {sensor_data['humidity_percent']}%
- Soil Moisture: {sensor_data['soil_moisture_percent']}%
- Plant Health: {sensor_data['plant_health_index']}/100
- Pest Pressure: {sensor_data['pest_pressure_index']}/10

You have access to all sensor data and can answer questions about the farm status,
give advice, interpret readings, and recommend actions. Be conversational, helpful,
and specific. Reference actual sensor values when relevant."""

    messages = conversation_history + [{"role": "user", "content": user_message}]

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=messages
    ) as stream:
        for text in stream.text_stream:
            yield text
