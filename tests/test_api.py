def test_health_is_public(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_generate_requires_authentication(client, payload):
    response = client.post("/v1/resumes/generate", json=payload)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_generate_runs_complete_pipeline(client, payload):
    response = client.post("/v1/resumes/generate", json=payload, headers={"X-API-Key": "test-key"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["profile_analysis"]["candidate_level"] == "Mid-Level"
    assert body["resume"]["professional_summary"]
    assert body["review"]["quality_score"] >= 80
    assert body["metadata"]["agents_executed"] == [
        "profile_analyzer",
        "ats_optimizer",
        "resume_writer",
        "reviewer",
    ]
    assert response.headers["X-Request-ID"] == body["metadata"]["request_id"]
    assert body["metadata"]["ai_provider"] == "deterministic"
    assert body["metadata"]["fallback_used"] is False


def test_invalid_input_returns_safe_error(client, payload):
    payload["profile"]["email"] = "not-an-email"
    response = client.post("/v1/resumes/generate", json=payload, headers={"X-API-Key": "test-key"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "not-an-email" not in response.text


def test_unknown_fields_are_rejected(client, payload):
    payload["unexpected"] = "ignored?"
    response = client.post("/v1/resumes/generate", json=payload, headers={"X-API-Key": "test-key"})
    assert response.status_code == 422
