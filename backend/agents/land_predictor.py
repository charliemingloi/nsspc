import json
from typing import AsyncIterator
from openai import AsyncOpenAI

SYSTEM_PROMPT = """You are an expert agricultural land analyst and farm planning consultant with 30+ years of experience.
Your role is to analyze land characteristics provided by farmers and generate comprehensive, data-driven farm setup predictions.

When analyzing land, you consider:
- Soil composition, pH, and nutrient levels
- Climate zone and seasonal patterns
- Water availability and irrigation needs
- Topography and drainage
- Local market demand
- Budget constraints and ROI timelines
- Sustainable farming practices

Always provide:
1. Top 3-5 recommended crops with confidence scores (%)
2. Predicted yield ranges per hectare
3. ROI estimates with payback periods
4. Required soil amendments and costs
5. Irrigation system recommendations
6. Risk factors and mitigation strategies
7. 12-month planting and harvest calendar

Be specific, practical, and optimistic but realistic. Format your response with clear sections."""

PREDICTION_TOOL = {
    "type": "function",
    "function": {
        "name": "generate_farm_prediction",
        "description": "Generate a structured farm prediction report based on land analysis",
        "parameters": {
            "type": "object",
            "properties": {
                "overall_suitability_score": {
                    "type": "number",
                    "description": "Overall land suitability score 0-100"
                },
                "recommended_crops": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "confidence": {"type": "number"},
                            "yield_per_hectare": {"type": "string"},
                            "annual_revenue_estimate": {"type": "string"},
                            "growing_season_months": {"type": "number"},
                            "difficulty": {"type": "string", "enum": ["Easy", "Moderate", "Advanced"]}
                        },
                        "required": ["name", "confidence", "yield_per_hectare", "annual_revenue_estimate", "growing_season_months", "difficulty"]
                    }
                },
                "soil_amendments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "amendment": {"type": "string"},
                            "quantity": {"type": "string"},
                            "estimated_cost": {"type": "string"},
                            "priority": {"type": "string", "enum": ["Critical", "High", "Medium", "Low"]}
                        }
                    }
                },
                "irrigation_recommendation": {
                    "type": "object",
                    "properties": {
                        "system_type": {"type": "string"},
                        "estimated_cost": {"type": "string"},
                        "water_requirement_daily": {"type": "string"},
                        "efficiency_rating": {"type": "string"}
                    }
                },
                "roi_analysis": {
                    "type": "object",
                    "properties": {
                        "initial_investment": {"type": "string"},
                        "monthly_operating_cost": {"type": "string"},
                        "expected_monthly_revenue": {"type": "string"},
                        "payback_period_months": {"type": "number"},
                        "year1_roi_percent": {"type": "number"},
                        "year3_roi_percent": {"type": "number"}
                    }
                },
                "risk_factors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "risk": {"type": "string"},
                            "severity": {"type": "string", "enum": ["High", "Medium", "Low"]},
                            "mitigation": {"type": "string"}
                        }
                    }
                },
                "planting_calendar": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "month": {"type": "string"},
                            "activities": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "summary": {"type": "string"},
                "quick_wins": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": [
                "overall_suitability_score", "recommended_crops", "soil_amendments",
                "irrigation_recommendation", "roi_analysis", "risk_factors",
                "planting_calendar", "summary", "quick_wins"
            ]
        }
    }
}


def _build_land_message(land_data: dict) -> str:
    return f"""Please analyze this land and provide a comprehensive farm setup prediction:

**Land Details:**
- Location/Region: {land_data.get('location', 'Not specified')}
- Land Area: {land_data.get('area', 'Not specified')} hectares
- Soil Type: {land_data.get('soil_type', 'Not specified')}
- Current Soil pH: {land_data.get('soil_ph', 'Unknown')}
- Climate Zone: {land_data.get('climate', 'Not specified')}
- Annual Rainfall: {land_data.get('rainfall', 'Not specified')} mm
- Water Source: {land_data.get('water_source', 'Not specified')}
- Current Land Use: {land_data.get('current_use', 'Unused/fallow')}
- Topography: {land_data.get('topography', 'Flat')}
- Available Budget: ${land_data.get('budget', 'Not specified')}
- Farming Experience: {land_data.get('experience', 'Beginner')}
- Preferred Crops: {land_data.get('preferred_crops', 'Open to suggestions')}
- Goals: {land_data.get('goals', 'General farming')}

Generate a full prediction using the generate_farm_prediction function."""


async def predict_land(client: AsyncOpenAI, land_data: dict) -> dict:
    response = await client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        tools=[PREDICTION_TOOL],
        tool_choice={"type": "function", "function": {"name": "generate_farm_prediction"}},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_land_message(land_data)}
        ]
    )

    tool_call = response.choices[0].message.tool_calls[0]
    return json.loads(tool_call.function.arguments)


async def stream_land_analysis(client: AsyncOpenAI, land_data: dict) -> AsyncIterator[str]:
    user_message = f"""Provide a detailed narrative analysis of this farm land:

Location: {land_data.get('location', 'Not specified')}
Area: {land_data.get('area', 'Not specified')} hectares
Soil Type: {land_data.get('soil_type', 'Not specified')}
Climate: {land_data.get('climate', 'Not specified')}
Water Source: {land_data.get('water_source', 'Not specified')}
Budget: ${land_data.get('budget', 'Not specified')}
Experience Level: {land_data.get('experience', 'Beginner')}
Goals: {land_data.get('goals', 'General profitable farming')}

Provide an expert, encouraging, and practical analysis."""

    stream = await client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1024,
        stream=True,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )

    async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content
