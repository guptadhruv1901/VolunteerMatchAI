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
