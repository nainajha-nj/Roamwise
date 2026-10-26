from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def payload(**overrides):
    data = {"destination":"Darjeeling", "duration_days":3, "travellers":2, "budget":18000,
            "currency":"INR", "party_type":"couple", "travel_style":"culture", "pace":"balanced",
            "interests":["food", "sightseeing"], "accommodation":"mid-range"}
    data.update(overrides)
    return data

def test_health():
    r = client.get('/api/health')
    assert r.status_code == 200 and r.json()['status'] == 'ok'

def test_generate_itinerary_days_and_fields():
    r = client.post('/api/itineraries/generate', json=payload())
    assert r.status_code == 200
    data = r.json()
    assert data['duration_days'] == 3
    assert len(data['days']) == 3
    assert data['destination'] == 'Darjeeling'
    assert data['budget']['total'] <= 18000
    assert data['days'][0]['activities']

def test_reject_invalid_duration():
    r = client.post('/api/itineraries/generate', json=payload(duration_days=0))
    assert r.status_code == 422
