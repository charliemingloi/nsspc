import os
import json
import asyncio
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

import anthropic
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from agents.land_predictor import predict_land, stream_land_analysis
from agents.farm_monitor import generate_sensor_data, generate_historical_data, analyze_farm_status, chat_about_farm
from agents.agri_chat import route_to_agents, stream_agent_response, get_agents_info
from agents.product_bot import product_bot_chat, get_catalog_summary

load_dotenv()

DATA_FILE = Path(__file__).parent / "data" / "farms.json"
DATA_FILE.parent.mkdir(exist_ok=True)


def load_farms() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"farms": {}, "conversations": {}}


def save_farms(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")
    return anthropic.Anthropic(api_key=api_key)


app = FastAPI(title="AgroSmart AI Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request Models ────────────────────────────────────────────────────────────

class LandData(BaseModel):
    location: str = ""
    area: str = ""
    soil_type: str = ""
    soil_ph: str = ""
    climate: str = ""
    rainfall: str = ""
    water_source: str = ""
    current_use: str = ""
    topography: str = "Flat"
    budget: str = ""
    experience: str = "Beginner"
    preferred_crops: str = ""
    goals: str = ""


class FarmProfile(BaseModel):
    name: str
    location: str = ""
    area: str = ""
    crops: str = ""
    growth_stage: str = "Vegetative"
    days_planted: str = ""
    experience: str = "Beginner"


class ChatMessage(BaseModel):
    message: str
    conversation_id: str = "default"
    farm_id: Optional[str] = None


class FarmChatMessage(BaseModel):
    message: str
    farm_id: str
    conversation_id: str = "default"


class ObservationRequest(BaseModel):
    farm_id: str
    observations: str = ""


# ─── API Routes ────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    key_set = bool(os.environ.get("ANTHROPIC_API_KEY"))
    return {"status": "ok", "api_key_configured": key_set}


# Land Prediction endpoints
@app.post("/api/predict-land")
async def predict_land_endpoint(land_data: LandData):
    client = get_client()
    result = await predict_land(client, land_data.model_dump())
    return result


@app.post("/api/predict-land/stream")
async def predict_land_stream(land_data: LandData):
    client = get_client()

    async def generate():
        async for chunk in stream_land_analysis(client, land_data.model_dump()):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# Farm management endpoints
@app.post("/api/farms")
async def create_farm(profile: FarmProfile):
    data = load_farms()
    farm_id = f"farm_{len(data['farms']) + 1}_{profile.name.replace(' ', '_').lower()}"
    data["farms"][farm_id] = profile.model_dump()
    save_farms(data)
    return {"farm_id": farm_id, "profile": profile.model_dump()}


@app.get("/api/farms")
async def list_farms():
    data = load_farms()
    return {"farms": data["farms"]}


@app.get("/api/farms/{farm_id}")
async def get_farm(farm_id: str):
    data = load_farms()
    if farm_id not in data["farms"]:
        raise HTTPException(status_code=404, detail="Farm not found")
    return data["farms"][farm_id]


# Farm monitoring endpoints
@app.get("/api/farms/{farm_id}/sensors")
async def get_sensor_data(farm_id: str):
    data = load_farms()
    if farm_id not in data["farms"]:
        raise HTTPException(status_code=404, detail="Farm not found")
    farm_profile = data["farms"][farm_id]
    sensor_data = generate_sensor_data(farm_profile)
    historical = generate_historical_data(7)
    return {"sensor_data": sensor_data, "historical": historical}


@app.post("/api/farms/{farm_id}/analyze")
async def analyze_farm(farm_id: str, request: ObservationRequest):
    data = load_farms()
    if farm_id not in data["farms"]:
        raise HTTPException(status_code=404, detail="Farm not found")

    farm_profile = data["farms"][farm_id]
    client = get_client()
    sensor_data = generate_sensor_data(farm_profile)
    historical = generate_historical_data(7)

    async def generate():
        async for chunk in analyze_farm_status(client, farm_profile, sensor_data, historical, request.observations):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/farms/{farm_id}/chat")
async def farm_chat(farm_id: str, chat: FarmChatMessage):
    data = load_farms()
    if farm_id not in data["farms"]:
        raise HTTPException(status_code=404, detail="Farm not found")

    farm_profile = data["farms"][farm_id]
    client = get_client()
    sensor_data = generate_sensor_data(farm_profile)

    # Load conversation history
    conv_key = f"farm_{farm_id}_{chat.conversation_id}"
    history = data.get("conversations", {}).get(conv_key, [])

    full_response = []

    async def generate():
        async for chunk in chat_about_farm(client, farm_profile, sensor_data, history, chat.message):
            full_response.append(chunk)
            yield f"data: {json.dumps({'text': chunk})}\n\n"

        # Save conversation
        response_text = "".join(full_response)
        if "conversations" not in data:
            data["conversations"] = {}
        if conv_key not in data["conversations"]:
            data["conversations"][conv_key] = []
        data["conversations"][conv_key].append({"role": "user", "content": chat.message})
        data["conversations"][conv_key].append({"role": "assistant", "content": response_text})
        # Keep only last 20 messages
        data["conversations"][conv_key] = data["conversations"][conv_key][-20:]
        save_farms(data)

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# AgriChat endpoints
@app.get("/api/agri-chat/agents")
async def get_agents():
    return {"agents": get_agents_info()}


@app.post("/api/agri-chat/route")
async def route_message(chat: ChatMessage):
    client = get_client()
    routing = await route_to_agents(client, chat.message)
    return routing


@app.post("/api/agri-chat/stream")
async def agri_chat_stream(chat: ChatMessage):
    data = load_farms()
    client = get_client()

    # Route to appropriate agents
    routing = await route_to_agents(client, chat.message)
    agents_to_use = routing.get("agents", ["general"])

    # Load conversation history
    conv_key = f"agri_{chat.conversation_id}"
    history = data.get("conversations", {}).get(conv_key, [])

    full_responses = {}

    async def generate():
        for agent_id in agents_to_use:
            yield f"data: {json.dumps({'type': 'agent_start', 'agent_id': agent_id})}\n\n"
            agent_response = []

            async for chunk in stream_agent_response(client, agent_id, history, chat.message):
                agent_response.append(chunk)
                yield f"data: {json.dumps({'type': 'text', 'agent_id': agent_id, 'text': chunk})}\n\n"

            full_responses[agent_id] = "".join(agent_response)
            yield f"data: {json.dumps({'type': 'agent_end', 'agent_id': agent_id})}\n\n"

        # Save conversation (use first agent's response)
        if "conversations" not in data:
            data["conversations"] = {}
        if conv_key not in data["conversations"]:
            data["conversations"][conv_key] = []

        all_response = "\n\n".join(full_responses.values())
        data["conversations"][conv_key].append({"role": "user", "content": chat.message})
        data["conversations"][conv_key].append({"role": "assistant", "content": all_response})
        data["conversations"][conv_key] = data["conversations"][conv_key][-20:]
        save_farms(data)

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# Product Bot endpoints
@app.get("/api/products/catalog")
async def get_catalog():
    return get_catalog_summary()


@app.post("/api/products/chat")
async def product_chat(chat: ChatMessage):
    data = load_farms()
    client = get_client()

    # Get farm profile if provided
    farm_profile = None
    if chat.farm_id and chat.farm_id in data.get("farms", {}):
        farm_profile = data["farms"][chat.farm_id]

    # Load conversation history
    conv_key = f"product_{chat.conversation_id}"
    history = data.get("conversations", {}).get(conv_key, [])

    full_response = []

    async def generate():
        async for chunk in product_bot_chat(client, history, chat.message, farm_profile):
            full_response.append(chunk)
            yield f"data: {json.dumps({'text': chunk})}\n\n"

        # Save conversation
        response_text = "".join(full_response)
        if "conversations" not in data:
            data["conversations"] = {}
        if conv_key not in data["conversations"]:
            data["conversations"][conv_key] = []
        data["conversations"][conv_key].append({"role": "user", "content": chat.message})
        data["conversations"][conv_key].append({"role": "assistant", "content": response_text})
        data["conversations"][conv_key] = data["conversations"][conv_key][-20:]
        save_farms(data)

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# Serve frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(str(frontend_path / "index.html"))

    @app.get("/{path:path}")
    async def serve_frontend_routes(path: str):
        file_path = frontend_path / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_path / "index.html"))
