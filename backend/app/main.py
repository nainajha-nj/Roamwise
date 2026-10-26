import os
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import TripRequest, Itinerary, SaveTripRequest, UpdateTripRequest
from .planner import generate_plan
from . import store

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

@asynccontextmanager
async def lifespan(app: FastAPI):
    store.init_store()
    yield

app = FastAPI(title="RoamWise Travel Planner API", version="1.0.0", description="Personalized itinerary generation, trip persistence, and optional Gemini/Supabase integrations.", lifespan=lifespan)
origins = [x.strip() for x in os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=['GET','POST','PUT','DELETE','OPTIONS'], allow_headers=['*'])

@app.get('/api/health')
def health():
    return {"status":"ok", "service":"roamwise-api", "ai_provider":"gemini-with-fallback" if os.getenv('GEMINI_API_KEY') else "rules-engine", "storage":"supabase" if os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_SERVICE_ROLE_KEY') else "sqlite"}

@app.post('/api/itineraries/generate', response_model=Itinerary)
async def create_itinerary(request: TripRequest):
    return await generate_plan(request)

@app.get('/api/trips')
def trips():
    try: return {"items": store.list_trips()}
    except Exception as e: raise HTTPException(503, detail=f"Trip storage unavailable: {type(e).__name__}")

@app.post('/api/trips', response_model=Itinerary)
def save_trip(request: SaveTripRequest):
    try: return store.save_trip(request.itinerary.model_dump())
    except Exception as e: raise HTTPException(503, detail=f"Could not save trip: {type(e).__name__}")

@app.get('/api/trips/{trip_id}', response_model=Itinerary)
def get_trip(trip_id: str):
    try: data = store.get_trip(trip_id)
    except Exception as e: raise HTTPException(503, detail=f"Trip storage unavailable: {type(e).__name__}")
    if not data: raise HTTPException(404, detail='Trip not found')
    return data

@app.put('/api/trips/{trip_id}', response_model=Itinerary)
def update_trip(trip_id: str, request: UpdateTripRequest):
    try:
        if not store.get_trip(trip_id): raise HTTPException(404, detail='Trip not found')
        data = request.itinerary.model_dump(); data['id'] = trip_id
        return store.save_trip(data)
    except HTTPException: raise
    except Exception as e: raise HTTPException(503, detail=f"Could not update trip: {type(e).__name__}")

@app.delete('/api/trips/{trip_id}')
def remove_trip(trip_id: str):
    try: deleted = store.delete_trip(trip_id)
    except Exception as e: raise HTTPException(503, detail=f"Could not delete trip: {type(e).__name__}")
    if not deleted: raise HTTPException(404, detail='Trip not found')
    return {"deleted": True, "id": trip_id}
