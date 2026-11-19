import os
from uuid import uuid4
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
def profile():
    return client.post("/api/profiles", json={"name":"Ada","email":f"{uuid4()}@example.com","causes":["food"],"skills":["languages"],"availability":"flexible","location":"remote","accessibility_needs":[]}).json()
def test_health_and_contexts():
    assert client.get("/api/health").json()["status"] == "ok"
    assert len(client.get("/api/contexts").json()) >= 2
def test_duplicate_profile_email_returns_conflict():
    email = f"{uuid4()}@example.com"
    payload = {"name": "Duplicate", "email": email, "causes": ["education"], "location": "remote"}
    assert client.post("/api/profiles", json=payload).status_code == 201
    response = client.post("/api/profiles", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "A profile with this email already exists."

def test_recommend_completion_duplicate_and_history():
    p = profile()
    r = client.post("/api/recommendations", json={"profile_id":p["id"],"context_id":"quick"})
    assert r.status_code == 200 and r.json()["matched"]
    opportunity = r.json()["opportunity"]["id"]
    assert client.post("/api/completions", json={"profile_id":p["id"],"opportunity_id":opportunity}).status_code == 201
    assert client.post("/api/completions", json={"profile_id":p["id"],"opportunity_id":opportunity}).status_code == 201
    assert len(client.get(f"/api/history/{p['id']}").json()) >= 1
def test_no_match_for_unknown_cause():
    p = client.post("/api/profiles", json={"name":"No Match","email":f"{uuid4()}@example.com","causes":["ocean"],"location":"remote"}).json()
    result = client.post("/api/recommendations", json={"profile_id":p["id"],"context_id":"quick"}).json()
    assert result["matched"] is False

def test_context_constraints_and_structured_history():
    p = client.post("/api/profiles", json={
        "name": "Context User",
        "email": f"{uuid4()}@example.com",
        "causes": ["education"],
        "skills": ["teaching"],
        "location": "remote",
    }).json()
    context = client.post(f"/api/profiles/{p['id']}/contexts", json={
        "time": "1h",
        "energy": "medium",
        "environment": "indoors",
        "mode": "remote",
        "skills": ["teaching"],
        "equipment": ["laptop"],
        "causes": ["education"],
    })
    assert context.status_code == 201
    result = client.post("/api/recommendations", json={"profile_id": p["id"], "context_id": str(context.json()["id"])}).json()
    assert result["matched"] is True
    assert result["opportunity"]["duration_minutes"] <= 60
    assert result["opportunity"]["mode"] == "remote"
    assert result["opportunity"]["task_breakdown"]
    alternatives = client.post(f"/api/recommendations/{result['recommendation_id']}/alternatives")
    assert alternatives.status_code == 200
    assert all(item["id"] != result["opportunity"]["id"] for item in alternatives.json())
    assert client.post(f"/api/recommendations/{result['recommendation_id']}/completion").status_code == 201
    history = client.get(f"/api/profiles/{p['id']}/history").json()
    assert history["total_completed"] == 1
    assert history["total_minutes"] == result["opportunity"]["duration_minutes"]
