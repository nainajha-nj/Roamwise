from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

TravelStyle = Literal["balanced", "adventure", "culture", "relaxation", "foodie", "nature", "luxury"]
TravelPace = Literal["relaxed", "balanced", "packed"]
PartyType = Literal["solo", "couple", "group", "family"]

class TripRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    destination: str = Field(min_length=2, max_length=100)
    start_date: str | None = None
    duration_days: int = Field(default=3, ge=1, le=14)
    travellers: int = Field(default=1, ge=1, le=30)
    budget: float = Field(default=15000, gt=0, le=10_000_000)
    currency: str = "INR"
    party_type: PartyType = "solo"
    travel_style: TravelStyle = "balanced"
    pace: TravelPace = "balanced"
    interests: list[str] = Field(default_factory=lambda: ["sightseeing", "local food"])
    accommodation: str = "mid-range"
    notes: str = Field(default="", max_length=1000)

class Activity(BaseModel):
    time: str
    title: str
    description: str
    estimated_cost: float = 0
    category: str = "sightseeing"
    duration_hours: float = 1.0

class ItineraryDay(BaseModel):
    day: int
    title: str
    area: str
    activities: list[Activity]
    food_suggestion: str
    logistics: str
    estimated_day_cost: float

class BudgetBreakdown(BaseModel):
    transport: float
    stay: float
    food: float
    activities: float
    buffer: float
    total: float
    per_person: float

class Itinerary(BaseModel):
    id: str | None = None
    title: str
    destination: str
    summary: str
    duration_days: int
    travellers: int
    currency: str = "INR"
    source: str = "rules-engine"
    days: list[ItineraryDay]
    budget: BudgetBreakdown
    tips: list[str]
    created_at: str | None = None

class SaveTripRequest(BaseModel):
    itinerary: Itinerary

class UpdateTripRequest(BaseModel):
    itinerary: Itinerary
