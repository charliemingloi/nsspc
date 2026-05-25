import json
from typing import AsyncIterator
from openai import AsyncOpenAI

PRODUCT_CATALOG = {
    "seeds": [
        {"id": "S001", "name": "Hybrid Tomato F1 - Beefmaster", "brand": "AgroSeed Pro", "price_usd": 12.50, "unit": "per 100 seeds", "category": "seeds", "subcategory": "vegetables", "crop": "tomato", "features": ["High yield: 8-10kg per plant", "Disease resistant", "60-day maturity", "Heat tolerant"], "rating": 4.8, "in_stock": True},
        {"id": "S002", "name": "Non-GMO Sweet Corn - Golden Jubilee", "brand": "Heritage Seeds", "price_usd": 8.99, "unit": "per 500 seeds", "category": "seeds", "subcategory": "grains", "crop": "corn", "features": ["Extra sweet variety", "75-day maturity", "Heirloom quality", "Open-pollinated"], "rating": 4.6, "in_stock": True},
        {"id": "S003", "name": "Rice Variety IR64 - High Yield", "brand": "AgriGene", "price_usd": 25.00, "unit": "per kg", "category": "seeds", "subcategory": "grains", "crop": "rice", "features": ["130-day maturity", "Flood tolerant", "7-8 tons/ha yield", "Blast resistant"], "rating": 4.7, "in_stock": True},
        {"id": "S004", "name": "Organic Spinach - Bloomsdale", "brand": "Organic Roots", "price_usd": 6.50, "unit": "per 200 seeds", "category": "seeds", "subcategory": "leafy greens", "crop": "spinach", "features": ["Organic certified", "40-day maturity", "Cold hardy", "Bolting resistant"], "rating": 4.5, "in_stock": True},
        {"id": "S005", "name": "Chili Pepper - Thai Hot", "brand": "SpiceFarm Seeds", "price_usd": 9.99, "unit": "per 50 seeds", "category": "seeds", "subcategory": "vegetables", "crop": "chili", "features": ["Ultra hot variety", "90-day maturity", "High capsaicin", "Compact plant"], "rating": 4.4, "in_stock": True},
        {"id": "S006", "name": "Watermelon - Sugar Baby", "brand": "AgroSeed Pro", "price_usd": 7.50, "unit": "per 30 seeds", "category": "seeds", "subcategory": "fruits", "crop": "watermelon", "features": ["80-day maturity", "8-10 lb fruits", "Disease resistant", "Compact vine"], "rating": 4.6, "in_stock": True},
        {"id": "S007", "name": "Soybeans - High Protein DP 4917", "brand": "AgriGene", "price_usd": 45.00, "unit": "per 25 kg", "category": "seeds", "subcategory": "legumes", "crop": "soybean", "features": ["42% protein content", "Nitrogen-fixing", "110-day maturity", "Herbicide tolerant"], "rating": 4.5, "in_stock": True}
    ],
    "fertilizers": [
        {"id": "F001", "name": "Complete NPK 15-15-15 Granular", "brand": "NutriGrow", "price_usd": 35.00, "unit": "per 25 kg bag", "category": "fertilizers", "subcategory": "synthetic", "features": ["Balanced nutrition", "Slow release coating", "pH neutral", "All crops"], "rating": 4.7, "in_stock": True},
        {"id": "F002", "name": "Organic Fish & Seaweed Liquid", "brand": "OceanGrow", "price_usd": 28.50, "unit": "per 5L concentrate", "category": "fertilizers", "subcategory": "organic", "features": ["OMRI listed organic", "Natural growth stimulant", "Improves soil biology", "Foliar or soil drench"], "rating": 4.8, "in_stock": True},
        {"id": "F003", "name": "Urea 46% Nitrogen", "brand": "NitroFarm", "price_usd": 22.00, "unit": "per 25 kg", "category": "fertilizers", "subcategory": "nitrogen", "features": ["46% N content", "Fast acting", "Cost effective", "Leafy crop boost"], "rating": 4.5, "in_stock": True},
        {"id": "F004", "name": "Superphosphate 0-46-0", "brand": "PhosAgri", "price_usd": 30.00, "unit": "per 25 kg", "category": "fertilizers", "subcategory": "phosphorus", "features": ["High P for root development", "Water soluble", "Promotes flowering"], "rating": 4.6, "in_stock": True},
        {"id": "F005", "name": "Vermicompost Premium Grade", "brand": "EarthCycle", "price_usd": 18.00, "unit": "per 20 kg", "category": "fertilizers", "subcategory": "organic", "features": ["Worm castings", "Full microbiome", "Slow release 6 months", "pH neutral"], "rating": 4.9, "in_stock": True},
        {"id": "F006", "name": "Potassium Sulfate 0-0-50", "brand": "KaliGrow", "price_usd": 40.00, "unit": "per 25 kg", "category": "fertilizers", "subcategory": "potassium", "features": ["50% K2O", "Low chloride", "Fruit & root crops", "Improves quality"], "rating": 4.7, "in_stock": True},
        {"id": "F007", "name": "Calcium Nitrate - Foliar Grade", "brand": "CalciMax", "price_usd": 32.00, "unit": "per 25 kg", "category": "fertilizers", "subcategory": "secondary nutrients", "features": ["Prevents blossom end rot", "Fast uptake", "Strengthens cell walls"], "rating": 4.8, "in_stock": True}
    ],
    "pesticides": [
        {"id": "P001", "name": "Neem Oil Concentrate - Organic", "brand": "GreenShield", "price_usd": 22.00, "unit": "per 500ml", "category": "pesticides", "subcategory": "organic insecticide", "features": ["OMRI organic certified", "Controls 200+ pests", "Fungicide + insecticide", "Safe for beneficials"], "rating": 4.7, "in_stock": True},
        {"id": "P002", "name": "Bacillus thuringiensis (Bt) Spray", "brand": "BioDefend", "price_usd": 35.00, "unit": "per 1L", "category": "pesticides", "subcategory": "biological", "features": ["Caterpillar specific", "Organic approved", "Safe for bees", "Rain-fast formula"], "rating": 4.6, "in_stock": True},
        {"id": "P003", "name": "Copper Fungicide Wettable Powder", "brand": "FungoClear", "price_usd": 28.00, "unit": "per 500g", "category": "pesticides", "subcategory": "fungicide", "features": ["Broad spectrum", "Controls blight/mildew", "Multi-crop approved"], "rating": 4.5, "in_stock": True},
        {"id": "P004", "name": "Diatomaceous Earth - Food Grade", "brand": "EarthGuard", "price_usd": 16.50, "unit": "per 2 kg", "category": "pesticides", "subcategory": "mechanical", "features": ["100% non-toxic", "Kills crawling insects", "Safe for humans & pets", "Long lasting"], "rating": 4.8, "in_stock": True},
        {"id": "P005", "name": "Glyphosate 41% - Weed Control", "brand": "WeedAway Pro", "price_usd": 45.00, "unit": "per 5L", "category": "pesticides", "subcategory": "herbicide", "features": ["Non-selective herbicide", "Pre-planting use", "7-day re-entry"], "rating": 4.3, "in_stock": True}
    ],
    "irrigation": [
        {"id": "I001", "name": "Drip Irrigation Kit - 100 Plants", "brand": "AquaPrecise", "price_usd": 89.00, "unit": "complete kit", "category": "irrigation", "subcategory": "drip system", "features": ["90% water efficiency", "Timer included", "Expandable", "Pressure regulated"], "rating": 4.8, "in_stock": True},
        {"id": "I002", "name": "Sprinkler System - 500m² Coverage", "brand": "RainMaker Pro", "price_usd": 145.00, "unit": "complete system", "category": "irrigation", "subcategory": "sprinkler", "features": ["360° coverage", "Adjustable head", "Auto pressure", "Winter resistant"], "rating": 4.6, "in_stock": True},
        {"id": "I003", "name": "Smart Irrigation Controller WiFi", "brand": "SmartFarm Tech", "price_usd": 75.00, "unit": "per unit", "category": "irrigation", "subcategory": "automation", "features": ["Weather-based scheduling", "Smartphone control", "8-zone control", "Water savings analytics"], "rating": 4.9, "in_stock": True},
        {"id": "I004", "name": "Soil Moisture Sensor Set (4 sensors)", "brand": "AgroSense", "price_usd": 120.00, "unit": "set of 4", "category": "irrigation", "subcategory": "sensors", "features": ["Real-time monitoring", "Bluetooth enabled", "App integration", "Weatherproof"], "rating": 4.7, "in_stock": True}
    ],
    "soil_amendments": [
        {"id": "A001", "name": "Agricultural Lime - Calcite", "brand": "SoilBalance", "price_usd": 15.00, "unit": "per 25 kg", "category": "soil_amendments", "subcategory": "pH adjuster", "features": ["Raises soil pH", "Adds calcium", "Improves structure", "Long lasting"], "rating": 4.6, "in_stock": True},
        {"id": "A002", "name": "Sulfur Granular - pH Lowering", "brand": "AcidFarm", "price_usd": 18.00, "unit": "per 10 kg", "category": "soil_amendments", "subcategory": "pH adjuster", "features": ["Lowers soil pH", "Elemental sulfur", "Slow acting 6-8 weeks"], "rating": 4.5, "in_stock": True},
        {"id": "A003", "name": "Biochar Premium - Activated", "brand": "CarbonFarm", "price_usd": 42.00, "unit": "per 10 kg", "category": "soil_amendments", "subcategory": "organic matter", "features": ["Permanent carbon storage", "Improves water retention", "Nutrient retention", "Microbiome habitat"], "rating": 4.9, "in_stock": True},
        {"id": "A004", "name": "Mycorrhizal Inoculant - Root Builder", "brand": "MycoForce", "price_usd": 35.00, "unit": "per 500g", "category": "soil_amendments", "subcategory": "biological", "features": ["14 species blend", "Extends root network", "Drought resistance", "Nutrient uptake boost"], "rating": 4.8, "in_stock": True},
        {"id": "A005", "name": "Perlite Horticultural Grade", "brand": "LightGrow", "price_usd": 24.00, "unit": "per 20L bag", "category": "soil_amendments", "subcategory": "structure", "features": ["Improves drainage", "Aerates soil", "pH neutral", "Reusable"], "rating": 4.7, "in_stock": True}
    ],
    "equipment": [
        {"id": "E001", "name": "Multi-Parameter Soil Tester", "brand": "AgroSense Pro", "price_usd": 55.00, "unit": "per unit", "category": "equipment", "subcategory": "testing", "features": ["pH, moisture, light, temperature", "Instant readings", "No batteries needed", "Field grade"], "rating": 4.5, "in_stock": True},
        {"id": "E002", "name": "Backpack Sprayer 16L - Pro Grade", "brand": "SprayMaster", "price_usd": 68.00, "unit": "per unit", "category": "equipment", "subcategory": "application", "features": ["Ergonomic design", "Anti-drip nozzle", "Adjustable pressure", "Chemical resistant"], "rating": 4.7, "in_stock": True},
        {"id": "E003", "name": "Soil Thermometer Digital", "brand": "TempCheck", "price_usd": 18.50, "unit": "per unit", "category": "equipment", "subcategory": "monitoring", "features": ["Instant read", "12\" probe", "°C/°F switchable", "Waterproof"], "rating": 4.6, "in_stock": True},
        {"id": "E004", "name": "Drone Agricultural Sprayer 10L", "brand": "AirFarm", "price_usd": 2800.00, "unit": "per unit", "category": "equipment", "subcategory": "precision ag", "features": ["GPS precision", "10L tank", "3 hectares/hour", "Obstacle avoidance"], "rating": 4.8, "in_stock": False},
        {"id": "E005", "name": "Weather Station Wireless - Farm Grade", "brand": "WeatherFarm", "price_usd": 195.00, "unit": "per station", "category": "equipment", "subcategory": "monitoring", "features": ["7 sensors", "Solar powered", "WiFi data logging", "1km range"], "rating": 4.9, "in_stock": True}
    ]
}

PRODUCT_BOT_SYSTEM = """You are AgriBot, an expert AI product advisor for AgroSmart Farming Supply.
You help farmers find the right products for their specific needs, farm conditions, and budget.

You have access to a catalog covering seeds, fertilizers, pest control, irrigation, soil amendments, and equipment.

Your approach:
1. Understand the farmer's specific situation
2. Use the search_products function to find relevant items
3. Recommend the most suitable products with clear reasoning
4. Prioritize organic/biological options when appropriate
5. Explain HOW to use recommended products
6. Suggest complementary products

Be friendly and help farmers make confident buying decisions.
Sign as "- AgriBot 🤖" """

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_products",
        "description": "Search the farming product catalog",
        "parameters": {
            "type": "object",
            "properties": {
                "categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Categories: seeds, fertilizers, pesticides, irrigation, soil_amendments, equipment"
                },
                "crop": {"type": "string", "description": "Specific crop if applicable"},
                "keywords": {"type": "array", "items": {"type": "string"}, "description": "Keywords to match"},
                "max_price": {"type": "number", "description": "Maximum price in USD"},
                "organic_only": {"type": "boolean", "description": "Only organic products"}
            },
            "required": ["categories"]
        }
    }
}


def search_products(categories: list, crop: str = None, keywords: list = None, max_price: float = None, organic_only: bool = False) -> list:
    results = []
    for category in categories:
        if category in PRODUCT_CATALOG:
            for product in PRODUCT_CATALOG[category]:
                if crop and "crop" in product and product["crop"].lower() != crop.lower():
                    continue
                if max_price and product["price_usd"] > max_price:
                    continue
                if organic_only and "organic" not in product.get("subcategory", "").lower() and \
                   not any("organic" in f.lower() or "omri" in f.lower() for f in product.get("features", [])):
                    continue
                if keywords:
                    text = f"{product['name']} {product.get('subcategory', '')} {' '.join(product.get('features', []))}".lower()
                    if not any(kw.lower() in text for kw in keywords):
                        continue
                results.append(product)
    return results


async def product_bot_chat(
    client: AsyncOpenAI,
    conversation_history: list,
    user_message: str,
    farm_profile: dict = None
) -> AsyncIterator[str]:
    farm_context = ""
    if farm_profile:
        farm_context = f"\nFarmer profile: growing {farm_profile.get('crops', 'various')}, {farm_profile.get('area', 'unknown')} ha, {farm_profile.get('experience', 'beginner')} experience."

    system = PRODUCT_BOT_SYSTEM + farm_context
    messages = [{"role": "system", "content": system}] + conversation_history + [{"role": "user", "content": user_message}]

    # First call — may use tool
    response = await client.chat.completions.create(
        model="gpt-4o",
        max_tokens=2000,
        tools=[SEARCH_TOOL],
        messages=messages
    )

    if response.choices[0].finish_reason == "tool_calls":
        tool_call = response.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        search_results = search_products(**args)

        # Build continuation messages with tool result
        messages_with_tool = messages + [
            response.choices[0].message,  # assistant message with tool_calls
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(search_results)
            }
        ]

        stream = await client.chat.completions.create(
            model="gpt-4o",
            max_tokens=2000,
            stream=True,
            messages=messages_with_tool
        )

        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    else:
        # Direct response
        content = response.choices[0].message.content or ""
        yield content


def get_catalog_summary() -> dict:
    return {
        cat: {
            "count": len(products),
            "items": [{"id": p["id"], "name": p["name"], "price": p["price_usd"], "rating": p["rating"]} for p in products]
        }
        for cat, products in PRODUCT_CATALOG.items()
    }
