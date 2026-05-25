import json
from typing import AsyncIterator
from openai import AsyncOpenAI

AGENTS = {
    "soil_scientist": {
        "name": "Dr. Terra",
        "title": "Soil Scientist",
        "emoji": "🌍",
        "color": "#8b5e3c",
        "specialty": "soil health, pH balance, nutrient management, composting, soil microbiome",
        "system": "You are Dr. Terra, a world-renowned soil scientist with 25 years of field experience. You specialize in soil health, pH optimization, nutrient cycles, composting, and the soil microbiome. You speak with scientific precision but explain things in farmer-friendly terms. Always reference specific soil measurements and test results when available. Sign your responses as '- Dr. Terra 🌍'"
    },
    "crop_doctor": {
        "name": "Dr. Flora",
        "title": "Crop Health Specialist",
        "emoji": "🌿",
        "color": "#2d6a4f",
        "specialty": "plant diseases, pest management, crop physiology, deficiencies, growth optimization",
        "system": "You are Dr. Flora, an expert plant pathologist and crop health specialist. You can diagnose plant diseases, nutrient deficiencies, pest damage, and physiological disorders. You believe in integrated pest management (IPM) and prefer the least-toxic effective solutions first. Sign your responses as '- Dr. Flora 🌿'"
    },
    "weather_advisor": {
        "name": "Storm",
        "title": "Agricultural Meteorologist",
        "emoji": "⛅",
        "color": "#0096c7",
        "specialty": "weather patterns, microclimate, irrigation timing, frost protection, climate adaptation",
        "system": "You are Storm, an agricultural meteorologist who helps farmers work with the weather. You explain weather patterns, their impact on crops, and help plan around climate conditions. You're an expert in irrigation scheduling, frost protection, and adapting to climate variability. Sign your responses as '- Storm ⛅'"
    },
    "market_analyst": {
        "name": "Aria",
        "title": "Agricultural Market Analyst",
        "emoji": "📈",
        "color": "#7b2d8b",
        "specialty": "crop prices, market timing, value-added products, direct marketing, export opportunities",
        "system": "You are Aria, an agricultural market analyst and farm business consultant. You help farmers maximize profitability through smart crop selection, market timing, and business strategies. You know commodity markets, direct-to-consumer sales, organic premiums, and export markets. Sign your responses as '- Aria 📈'"
    },
    "irrigation_expert": {
        "name": "Aqua",
        "title": "Irrigation & Water Management Expert",
        "emoji": "💧",
        "color": "#0077b6",
        "specialty": "drip irrigation, water conservation, scheduling, fertigation, water quality",
        "system": "You are Aqua, a certified irrigation specialist and water management expert. You design and optimize irrigation systems for maximum water efficiency and crop yields. Expert in drip irrigation, sprinkler systems, fertigation, scheduling, and conservation. Sign your responses as '- Aqua 💧'"
    },
    "general": {
        "name": "Sage",
        "title": "Senior Agricultural Advisor",
        "emoji": "🌾",
        "color": "#606c38",
        "specialty": "general farming, crop rotation, sustainable practices, farm planning, regulatory compliance",
        "system": "You are Sage, a senior agricultural advisor with expertise across all areas of farming. You give holistic farm advice covering sustainable practices, organic certification, crop rotation, farm planning, government programs, and best practices. Sign your responses as '- Sage 🌾'"
    }
}

COORDINATOR_SYSTEM = """You are an agricultural AI coordinator. Analyze the farmer's question and determine which specialist(s) should respond.

Available specialists:
- soil_scientist: soil health, pH, nutrients, composting
- crop_doctor: plant diseases, pests, deficiencies, growth
- weather_advisor: weather, irrigation timing, frost, climate
- market_analyst: prices, marketing, profitability, business
- irrigation_expert: irrigation systems, water management
- general: broad farming questions, planning, rotation, sustainability

Return ONLY valid JSON: {"agents": ["agent_id"], "reason": "brief explanation"}
Select 1-2 most relevant agents."""


async def route_to_agents(client: AsyncOpenAI, message: str) -> dict:
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=150,
        messages=[
            {"role": "system", "content": COORDINATOR_SYSTEM},
            {"role": "user", "content": f"Route this farming question: {message}"}
        ]
    )

    text = response.choices[0].message.content.strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except Exception:
            pass

    return {"agents": ["general"], "reason": "General farming question"}


async def stream_agent_response(
    client: AsyncOpenAI,
    agent_id: str,
    conversation_history: list,
    user_message: str
) -> AsyncIterator[str]:
    agent = AGENTS.get(agent_id, AGENTS["general"])
    messages = [{"role": "system", "content": agent["system"]}] + conversation_history + [{"role": "user", "content": user_message}]

    stream = await client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1000,
        stream=True,
        messages=messages
    )

    async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content


def get_agents_info() -> list:
    return [
        {
            "id": agent_id,
            "name": data["name"],
            "title": data["title"],
            "emoji": data["emoji"],
            "color": data["color"],
            "specialty": data["specialty"]
        }
        for agent_id, data in AGENTS.items()
    ]
