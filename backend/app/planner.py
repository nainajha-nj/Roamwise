import json, os, re
from datetime import datetime, timezone
from uuid import uuid4
import httpx
from .models import TripRequest, Itinerary, ItineraryDay, Activity, BudgetBreakdown

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

DESTINATION_SEEDS = {
    "darjeeling": ["Tiger Hill sunrise", "Batasia Loop", "Darjeeling Himalayan Railway", "Tea garden walk", "Peace Pagoda", "Chowrasta and Mall Road"],
    "gangtok": ["MG Marg promenade", "Enchey Monastery", "Tashi View Point", "Namgyal Institute of Tibetology", "Hanuman Tok", "Local market walk"],
    "jaipur": ["Amber Fort", "Hawa Mahal viewpoint", "City Palace", "Jantar Mantar", "Johari Bazaar", "Traditional Rajasthani dinner"],
    "goa": ["Old Goa heritage walk", "Fontainhas lanes", "Beach sunset", "Local seafood cafe", "Fort viewpoint", "Market stroll"],
    "kolkata": ["Victoria Memorial grounds", "College Street book walk", "Kumartuli artisan lanes", "Indian Museum", "Prinsep Ghat sunset", "Bengali food trail"],
    "siliguri": ["Salugara Monastery", "Hong Kong Market", "Mahananda Wildlife Sanctuary area", "Local food walk", "Sevoke viewpoint", "Tea garden visit"],
    "munnar": ["Tea museum", "Tea plantation viewpoint", "Mattupetty Dam", "Echo Point", "Local spice garden", "Sunset viewpoint"],
    "default": ["Historic town centre walk", "Popular local viewpoint", "Museum or cultural landmark", "Local market exploration", "Nature walk or garden", "Neighbourhood food trail"]
}
STYLE_WORDS = {
 "adventure": ("Outdoor adventure", "Choose a guided activity suitable for the season and your fitness level."),
 "culture": ("Culture and heritage", "Check opening hours and local etiquette before visiting religious or heritage sites."),
 "relaxation": ("Slow travel and relaxation", "Keep gaps between activities so the day stays restorative."),
 "foodie": ("Local food discovery", "Ask vendors about allergens and confirm dietary requirements."),
 "nature": ("Nature and scenic views", "Check weather and trail conditions before setting out."),
 "luxury": ("Comfort-first experience", "Reserve popular experiences in advance and confirm cancellation terms."),
 "balanced": ("A balanced local experience", "Mix one signature attraction with neighbourhood discoveries.")
}

def _budget(req: TripRequest) -> BudgetBreakdown:
    # Heuristic estimates, not live market prices. Budget is treated as total trip budget.
    days, people = req.duration_days, req.travellers
    style_factor = {"luxury": 1.7, "adventure": 1.08, "relaxation": 1.25, "foodie": 1.18, "culture": 1.0, "nature": 1.0, "balanced": 1.0}[req.travel_style]
    per_person_day = max(700, req.budget / max(1, days * people))
    # Allocate a fixed 10% contingency first, then normalize other categories so
    # even luxury/foodie preferences cannot push the estimate beyond the entered budget.
    weights = {
        "stay": 0.32 if req.accommodation == "budget" else 0.40 if req.accommodation == "mid-range" else 0.48,
        "food": 0.20 if req.travel_style != "foodie" else 0.25,
        "activities": 0.17 * style_factor,
        "transport": 0.15,
    }
    scale = (req.budget * 0.90) / sum(weights.values())
    stay = weights["stay"] * scale
    food = weights["food"] * scale
    activities = weights["activities"] * scale
    transport = weights["transport"] * scale
    buffer = req.budget * 0.10
    total = stay + food + activities + transport + buffer
    return BudgetBreakdown(transport=round(transport), stay=round(stay), food=round(food), activities=round(activities), buffer=round(buffer), total=round(req.budget), per_person=round(req.budget / people))

def fallback_plan(req: TripRequest) -> Itinerary:
    destination = req.destination.strip()
    key = destination.lower()
    seeds = DESTINATION_SEEDS.get(key, DESTINATION_SEEDS["default"])
    style_label, style_tip = STYLE_WORDS.get(req.travel_style, STYLE_WORDS["balanced"])
    per_day_budget = req.budget / req.duration_days
    days = []
    for i in range(req.duration_days):
        # Rotate attraction seeds to avoid repeating identical days on longer trips.
        names = [seeds[(i * 2 + j) % len(seeds)] for j in range(3)]
        multiplier = {"relaxed": 0.75, "balanced": 1.0, "packed": 1.2}[req.pace]
        activities = [
            Activity(time="09:00", title=names[0], description=f"Start with {names[0].lower()}; confirm local opening times before leaving.", estimated_cost=round(per_day_budget * .12), category="sightseeing", duration_hours=2),
            Activity(time="13:00", title=names[1], description=f"Explore {names[1].lower()} at a pace that fits your interests: {', '.join(req.interests[:3]) or req.travel_style}.", estimated_cost=round(per_day_budget * .10), category="experience", duration_hours=2),
            Activity(time="16:30" if req.pace != "packed" else "17:00", title=names[2], description=f"Finish with {names[2].lower()} and leave time for local travel and rest.", estimated_cost=round(per_day_budget * .08), category="local discovery", duration_hours=1.5),
        ]
        if req.pace == "relaxed": activities = activities[:2]
        if req.pace == "packed":
            activities.append(Activity(time="19:00", title="Evening food and neighbourhood walk", description="Try a well-reviewed local eatery and explore nearby streets safely.", estimated_cost=round(per_day_budget * .10), category="food", duration_hours=1.5))
        days.append(ItineraryDay(day=i+1, title=f"Day {i+1} · {style_label}", area=destination, activities=activities,
            food_suggestion=f"Look for a local restaurant serving regional specialities in {destination}; check recent reviews and dietary options.",
            logistics="Group nearby stops together, check current opening hours and weather, and allow extra transfer time.",
            estimated_day_cost=round(per_day_budget * multiplier)))
    budget = _budget(req)
    title = f"{req.duration_days}-day {destination} escape"
    summary = f"A {req.pace}-paced {req.travel_style} plan for {req.travellers} traveller(s), tailored around {', '.join(req.interests[:4]) or 'local discovery'} and a {req.currency} {req.budget:,.0f} total budget."
    return Itinerary(id=str(uuid4()), title=title, destination=destination, summary=summary, duration_days=req.duration_days,
        travellers=req.travellers, currency=req.currency, source="rules-engine", days=days, budget=budget,
        tips=[style_tip, "Prices are planning estimates, not live quotes; verify transport, entry fees, and accommodation directly.", "Keep a flexible backup for weather, closures, and unexpected delays.", "For group trips, agree on a daily meeting point and shared spending limit."],
        created_at=datetime.now(timezone.utc).isoformat())

def _extract_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start: raise ValueError("Gemini response did not contain a JSON object")
    return json.loads(text[start:end+1])

async def generate_plan(req: TripRequest) -> Itinerary:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key: return fallback_plan(req)
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    prompt = f'''You are RoamWise, a careful travel-planning assistant. Create a personalized itinerary from this JSON input: {req.model_dump_json()}.
Return ONLY valid JSON matching this shape: {{"title":"string","destination":"string","summary":"string","duration_days":integer,"travellers":integer,"currency":"INR","days":[{{"day":1,"title":"string","area":"string","activities":[{{"time":"09:00","title":"string","description":"string","estimated_cost":0,"category":"string","duration_hours":1}}],"food_suggestion":"string","logistics":"string","estimated_day_cost":0}}],"budget":{{"transport":0,"stay":0,"food":0,"activities":0,"buffer":0,"total":0,"per_person":0}},"tips":["string"]}}. Include exactly {req.duration_days} days. Costs must be plausible estimates in {req.currency}, total must not exceed {req.budget}, and clearly avoid claiming live availability. Use 2-4 activities per day, account for {req.pace} pace, party type {req.party_type}, style {req.travel_style}, and interests {req.interests}. Do not invent exact opening hours or live booking details.'''
    try:
        async with httpx.AsyncClient(timeout=35) as client:
            response = await client.post(GEMINI_URL.format(model=model, key=key), json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"responseMimeType":"application/json","temperature":0.65}})
            response.raise_for_status()
            payload = response.json()
            content = payload["candidates"][0]["content"]["parts"][0]["text"]
            data = _extract_json(content)
            data["id"] = str(uuid4()); data["source"] = "gemini"; data["created_at"] = datetime.now(timezone.utc).isoformat()
            # Ensure model output obeys key user constraints and schema.
            data["duration_days"] = req.duration_days; data["travellers"] = req.travellers; data["currency"] = req.currency
            itinerary = Itinerary.model_validate(data)
            if len(itinerary.days) != req.duration_days: raise ValueError("AI returned the wrong number of days")
            return itinerary
    except Exception:
        # Robust demo experience if the provider is unavailable or produces invalid output.
        return fallback_plan(req)
