import anthropic
from typing import AsyncIterator

AGENTS = {
    "soil_scientist": {
        "name": "Dr. Terra",
        "title": "Soil Scientist",
        "emoji": "🌍",
        "color": "#8b5e3c",
        "specialty": "soil health, pH balance, nutrient management, composting, soil microbiome",
        "system": """You are Dr. Terra, a world-renowned soil scientist with 25 years of field experience.
You specialize in soil health, pH optimization, nutrient cycles, composting, and the soil microbiome.
You speak with scientific precision but explain things in farmer-friendly terms.
Always reference specific soil measurements and test results when available.
You're passionate about building healthy soil as the foundation of all successful farming.
Sign your responses as "- Dr. Terra 🌍" """
    },
    "crop_doctor": {
        "name": "Dr. Flora",
        "title": "Crop Health Specialist",
        "emoji": "🌿",
        "color": "#2d6a4f",
        "specialty": "plant diseases, pest management, crop physiology, deficiencies, growth optimization",
        "system": """You are Dr. Flora, an expert plant pathologist and crop health specialist.
You can diagnose plant diseases, nutrient deficiencies, pest damage, and physiological disorders from descriptions and data.
You know the growth stages of hundreds of crops and what each crop needs at each stage.
You believe in integrated pest management (IPM) and prefer the least-toxic effective solutions first.
Sign your responses as "- Dr. Flora 🌿" """
    },
    "weather_advisor": {
        "name": "Storm",
        "title": "Agricultural Meteorologist",
        "emoji": "⛅",
        "color": "#0096c7",
        "specialty": "weather patterns, microclimate, irrigation timing, frost protection, climate adaptation",
        "system": """You are Storm, an agricultural meteorologist who helps farmers work with the weather.
You explain weather patterns, their impact on crops, and help farmers plan around climate conditions.
You're an expert in irrigation scheduling based on evapotranspiration, frost protection strategies,
and adapting to climate variability. You give practical, time-sensitive advice.
Sign your responses as "- Storm ⛅" """
    },
    "market_analyst": {
        "name": "Aria",
        "title": "Agricultural Market Analyst",
        "emoji": "📈",
        "color": "#7b2d8b",
        "specialty": "crop prices, market timing, value-added products, direct marketing, export opportunities",
        "system": """You are Aria, an agricultural market analyst and farm business consultant.
You help farmers maximize profitability through smart crop selection, market timing, and business strategies.
You know about commodity markets, direct-to-consumer sales, organic premiums, farm-to-table,
value-added processing, cooperatives, and export markets.
Sign your responses as "- Aria 📈" """
    },
    "irrigation_expert": {
        "name": "Aqua",
        "title": "Irrigation & Water Management Expert",
        "emoji": "💧",
        "color": "#0077b6",
        "specialty": "drip irrigation, water conservation, scheduling, fertigation, water quality",
        "system": """You are Aqua, a certified irrigation specialist and water management expert.
You design and optimize irrigation systems for maximum water efficiency and crop yields.
You're an expert in drip irrigation, sprinkler systems, fertigation, water quality,
scheduling based on crop needs, and water conservation techniques.
Sign your responses as "- Aqua 💧" """
    },
    "general": {
        "name": "Sage",
        "title": "Senior Agricultural Advisor",
        "emoji": "🌾",
        "color": "#606c38",
        "specialty": "general farming, crop rotation, sustainable practices, farm planning, regulatory compliance",
        "system": """You are Sage, a senior agricultural advisor with expertise across all areas of farming.
You coordinate insights from multiple agricultural disciplines to give holistic farm advice.
You're knowledgeable about sustainable farming practices, organic certification, crop rotation,
farm planning, government programs, and agricultural best practices.
You're the go-to advisor for comprehensive farm management questions.
Sign your responses as "- Sage 🌾" """
    }
}

COORDINATOR_SYSTEM = """You are an agricultural AI coordinator. Your job is to:
1. Analyze the farmer's question
2. Determine which specialist(s) should respond
3. Return ONLY a JSON object with the routing decision

Available specialists:
- soil_scientist: soil health, pH, nutrients, composting
- crop_doctor: plant diseases, pests, deficiencies, growth
- weather_advisor: weather, irrigation timing, frost, climate
- market_analyst: prices, marketing, profitability, business
- irrigation_expert: irrigation systems, water management
- general: broad farming questions, planning, rotation, sustainability

Return format:
{"agents": ["agent_id"], "reason": "brief explanation"}

Select 1-2 most relevant agents. For complex multi-topic questions use "general" as one agent."""


async def route_to_agents(client: anthropic.Anthropic, message: str) -> dict:
    """Determine which agents should respond to a message."""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        system=COORDINATOR_SYSTEM,
        messages=[{"role": "user", "content": f"Route this farming question: {message}"}]
    )

    text = response.content[0].text.strip()
    # Extract JSON from response
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        import json
        try:
            return json.loads(text[start:end])
        except Exception:
            pass

    return {"agents": ["general"], "reason": "General farming question"}


async def stream_agent_response(
    client: anthropic.Anthropic,
    agent_id: str,
    conversation_history: list,
    user_message: str
) -> AsyncIterator[str]:
    """Stream response from a specific agent."""
    agent = AGENTS.get(agent_id, AGENTS["general"])

    messages = conversation_history + [{"role": "user", "content": user_message}]

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=[{"type": "text", "text": agent["system"], "cache_control": {"type": "ephemeral"}}],
        messages=messages
    ) as stream:
        for text in stream.text_stream:
            yield text


def get_agents_info() -> list:
    """Return info about all available agents."""
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
