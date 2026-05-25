import json
import random
import math
from datetime import datetime, timedelta
from typing import AsyncIterator
from openai import AsyncOpenAI

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
    now = datetime.now()
    hour = now.hour
    day_of_year = now.timetuple().tm_yday

    base_temp = 22 + 8 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    temp_variation = 6 * math.sin(2 * math.pi * (hour - 6) / 24)
    temperature = round(base_temp + temp_variation + random.uniform(-2, 2), 1)
    humidity = round(max(30, min(95, 75 - (temperature - 20) * 1.5 + random.uniform(-5, 5))), 1)
    soil_moisture = round(random.uniform(45, 75), 1)
    soil_ph = round(random.uniform(5.8, 7.2), 2)
    light_lux = max(0, int(80000 * math.sin(math.pi * (hour - 6) / 12) * random.uniform(0.7, 1.0))) if 6 <= hour <= 18 else 0
    nitrogen = round(random.uniform(150, 280), 1)
    phosphorus = round(random.uniform(30, 80), 1)
    potassium = round(random.uniform(120, 250), 1)
    wind_speed = round(random.uniform(0.5, 8.0), 1)
    rainfall_24h = round(random.uniform(0, 15), 1) if random.random() > 0.6 else 0
    co2_ppm = round(random.uniform(390, 450), 0)
    health_index = round(random.uniform(65, 95), 1)
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
    now = datetime.now()
    daily = []
    for d in range(days):
        day_data_temps = []
        day = now - timedelta(days=days - 1 - d)
        day_of_year = day.timetuple().tm_yday
        base_temp = 22 + 8 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
        for h in range(24):
            t = base_temp + 6 * math.sin(math.pi * (h - 6) / 12) + random.uniform(-1.5, 1.5)
            day_data_temps.append(t)
        daily.append({
            "date": day.strftime("%Y-%m-%d"),
            "avg_temp": round(sum(day_data_temps) / 24, 1),
            "avg_humidity": round(random.uniform(45, 80), 1),
            "avg_soil_moisture": round(random.uniform(45, 75), 1),
            "avg_health": round(random.uniform(65, 95), 1)
        })
    return daily


async def analyze_farm_status(
    client: AsyncOpenAI,
    farm_profile: dict,
    sensor_data: dict,
    historical: list,
    user_observations: str = ""
) -> AsyncIterator[str]:
    context = f"""
**Farm Profile:**
- Farm Name: {farm_profile.get('name', 'My Farm')}
- Crops Growing: {farm_profile.get('crops', 'Various')}
- Farm Size: {farm_profile.get('area', 'Unknown')} hectares
- Growing Stage: {farm_profile.get('growth_stage', 'Vegetative')}

**Current Sensor Readings (Live):**
- Temperature: {sensor_data['temperature_c']}°C
- Humidity: {sensor_data['humidity_percent']}%
- Soil Moisture: {sensor_data['soil_moisture_percent']}%
- Soil pH: {sensor_data['soil_ph']}
- Light Intensity: {sensor_data['light_lux']:,} lux
- Nitrogen: {sensor_data['nitrogen_ppm']} ppm
- Phosphorus: {sensor_data['phosphorus_ppm']} ppm
- Potassium: {sensor_data['potassium_ppm']} ppm
- Wind Speed: {sensor_data['wind_speed_ms']} m/s
- Rainfall (24h): {sensor_data['rainfall_24h_mm']} mm
- CO2: {sensor_data['co2_ppm']} ppm
- Plant Health Index: {sensor_data['plant_health_index']}/100
- Pest Pressure: {sensor_data['pest_pressure_index']}/10

**7-Day Trend:**
{json.dumps(historical, indent=2)}

**Farmer Observations:** {user_observations or 'None provided'}

Provide: overall health score, alerts, key findings, trend analysis, action items, positives, 3-day outlook."""

    stream = await client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1500,
        stream=True,
        messages=[
            {"role": "system", "content": MONITOR_SYSTEM_PROMPT},
            {"role": "user", "content": context}
        ]
    )

    async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content


async def chat_about_farm(
    client: AsyncOpenAI,
    farm_profile: dict,
    sensor_data: dict,
    conversation_history: list,
    user_message: str
) -> AsyncIterator[str]:
    system = f"""You are a knowledgeable farm advisor monitoring {farm_profile.get('name', 'this farm')} in real-time.

Current stats:
- Crops: {farm_profile.get('crops', 'Various')}
- Temperature: {sensor_data['temperature_c']}°C
- Humidity: {sensor_data['humidity_percent']}%
- Soil Moisture: {sensor_data['soil_moisture_percent']}%
- Plant Health: {sensor_data['plant_health_index']}/100
- Pest Pressure: {sensor_data['pest_pressure_index']}/10

Answer questions about farm status, interpret readings, and recommend actions."""

    messages = [{"role": "system", "content": system}] + conversation_history + [{"role": "user", "content": user_message}]

    stream = await client.chat.completions.create(
        model="gpt-4o",
        max_tokens=800,
        stream=True,
        messages=messages
    )

    async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content
