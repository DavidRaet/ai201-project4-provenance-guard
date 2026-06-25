import pytest
from unittest.mock import patch

import app as app_module
from app import app, limiter


@pytest.fixture(autouse=True)
def clear_state():
    """Reset audit log, content status, and rate-limit counters between every test."""
    app_module.audit_log.clear()
    app_module.content_status.clear()
    try:
        if limiter._storage is not None:
            limiter._storage.reset()
    except Exception:
        pass
    yield
    app_module.audit_log.clear()
    app_module.content_status.clear()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["RATELIMIT_ENABLED"] = False
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def submit_text(client, text="Some sample text for testing."):
    """Submit text and return the parsed JSON response."""
    with patch("app.llm_signal", return_value=0.5), \
         patch("app.stylometric_signal", return_value=0.5):
        resp = client.post("/submit", json={"text": text})
    return resp


# ---------------------------------------------------------------------------
# F — /submit endpoint
# ---------------------------------------------------------------------------

class TestSubmitEndpoint:

    def test_valid_text_returns_200_with_required_keys(self, client):
        """F1: Valid text returns 200 with all required response keys."""
        resp = submit_text(client)
        assert resp.status_code == 200
        data = resp.get_json()
        for key in ("content_id", "confidence_score", "label_key", "label_text", "label_detail"):
            assert key in data, f"Missing key: {key}"

    def test_empty_text_returns_400(self, client):
        """F2: Empty text string returns 400."""
        resp = client.post("/submit", json={"text": ""})
        assert resp.status_code == 400

    def test_missing_json_returns_400(self, client):
        """F3: Missing JSON body returns 400."""
        resp = client.post("/submit", content_type="application/json", data="")
        assert resp.status_code == 400

    def test_submit_writes_to_audit_log(self, client):
        """F4: A successful submit appends one classification entry to the audit log."""
        submit_text(client)
        assert len(app_module.audit_log) == 1
        entry = app_module.audit_log[0]
        assert entry["type"] == "classification"
        assert "content_id" in entry
        assert "timestamp" in entry
        assert "confidence_score" in entry
        assert "label_key" in entry


# ---------------------------------------------------------------------------
# G — /appeal endpoint
# ---------------------------------------------------------------------------

class TestAppealEndpoint:

    def test_missing_reasoning_returns_400(self, client):
        """G1: Missing 'reasoning' field returns 400."""
        resp = client.post("/appeal", json={"content_id": "fake-id"})
        assert resp.status_code == 400

    def test_empty_reasoning_returns_400(self, client):
        """G2: Empty 'reasoning' string returns 400."""
        resp = client.post("/appeal", json={"content_id": "fake-id", "reasoning": ""})
        assert resp.status_code == 400

    def test_unknown_content_id_returns_404(self, client):
        """G3: Unknown content_id returns 404."""
        resp = client.post("/appeal", json={"content_id": "does-not-exist", "reasoning": "I wrote this myself."})
        assert resp.status_code == 404

    def test_valid_appeal_returns_200_under_review(self, client):
        """G4: Valid appeal after a submit returns 200 with under_review status."""
        submit_resp = submit_text(client)
        content_id = submit_resp.get_json()["content_id"]

        resp = client.post("/appeal", json={"content_id": content_id, "reasoning": "I wrote this myself."})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "under_review"
        assert data["content_id"] == content_id

    def test_duplicate_appeal_returns_409(self, client):
        """G5: A second appeal while already under_review returns 409."""
        submit_resp = submit_text(client)
        content_id = submit_resp.get_json()["content_id"]

        client.post("/appeal", json={"content_id": content_id, "reasoning": "First appeal."})
        resp = client.post("/appeal", json={"content_id": content_id, "reasoning": "Second appeal."})
        assert resp.status_code == 409

    def test_appeal_appends_to_audit_log(self, client):
        """G6: A successful appeal appends an appeal entry to the audit log."""
        submit_resp = submit_text(client)
        content_id = submit_resp.get_json()["content_id"]

        client.post("/appeal", json={"content_id": content_id, "reasoning": "I wrote this."})

        appeal_entries = [e for e in app_module.audit_log if e["type"] == "appeal"]
        assert len(appeal_entries) == 1
        entry = appeal_entries[0]
        assert entry["content_id"] == content_id
        assert entry["status"] == "under_review"
        assert entry["reasoning"] == "I wrote this."


# ---------------------------------------------------------------------------
# H — /log endpoint
# ---------------------------------------------------------------------------

class TestLogEndpoint:

    def test_empty_log_returns_list(self, client):
        """H1: GET /log returns a JSON list (empty when nothing submitted)."""
        resp = client.get("/log")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

    def test_log_contains_classification_after_submit(self, client):
        """H2: After one submit, GET /log returns a list with one classification entry."""
        submit_text(client)
        resp = client.get("/log")
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["type"] == "classification"

    def test_log_contains_both_entries_after_submit_and_appeal(self, client):
        """H3: After submit + appeal, GET /log has two entries in order."""
        submit_resp = submit_text(client)
        content_id = submit_resp.get_json()["content_id"]
        client.post("/appeal", json={"content_id": content_id, "reasoning": "I wrote this."})

        resp = client.get("/log")
        data = resp.get_json()
        assert len(data) == 2
        assert data[0]["type"] == "classification"
        assert data[1]["type"] == "appeal"
