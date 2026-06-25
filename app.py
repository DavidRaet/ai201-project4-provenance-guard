import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.errors import RateLimitExceeded
from flask_limiter.util import get_remote_address

from signals import llm_signal, stylometric_signal, combine_signals, label_selector

load_dotenv()

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

audit_log = []       # chronological list of all classification and appeal entries
content_status = {}  # content_id → "classified" | "under_review"


@app.errorhandler(RateLimitExceeded)
def handle_rate_limit(e):
    return (
        jsonify(
            {
                "error": "Rate limit exceeded. Try again in 60 seconds.",
                "status": 429,
            }
        ),
        429,
    )


@app.route("/")
def home():
    return "Provenance Guard is running."


@app.route("/log", methods=["GET"])
@limiter.limit("30 per minute")
def get_log():
    return jsonify(audit_log)


@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute")
def submit():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid or missing JSON payload."}), 400

    text = data.get("text")

    if not text or not isinstance(text, str) or not text.strip():
        return (
            jsonify(
                {"error": "Missing required field: 'text' must be a non-empty string."}
            ),
            400,
        )

    llm_sig = llm_signal(text)
    stylo_signal = stylometric_signal(text)
    confidence_score = combine_signals(llm_sig, stylo_signal)
    label = label_selector(confidence_score)

    content_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    audit_log.append(
        {
            "content_id": content_id,
            "timestamp": timestamp,
            "type": "classification",
            "confidence_score": round(confidence_score, 4),
            "label_key": label["label_key"],
        }
    )
    content_status[content_id] = "classified"

    return jsonify(
        {
            "content_id": content_id,
            "confidence_score": round(confidence_score, 4),
            "label_key": label["label_key"],
            "label_text": label["label_text"],
            "label_detail": label["label_detail"],
        }
    )


@app.route("/appeal", methods=["POST"])
@limiter.limit("5 per minute")
def appeal():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid or missing JSON payload."}), 400

    content_id = data.get("content_id")
    reasoning = data.get("reasoning")

    if not reasoning or not isinstance(reasoning, str) or not reasoning.strip():
        return jsonify({"error": "Missing required field: 'reasoning' must be a non-empty string."}), 400

    if not content_id:
        return jsonify({"error": "Missing required field: 'content_id'."}), 400

    if content_id not in content_status:
        return jsonify({"error": f"Content ID '{content_id}' not found."}), 404

    if content_status[content_id] == "under_review":
        return jsonify({"error": "An appeal for this content is already under review."}), 409

    content_status[content_id] = "under_review"
    audit_log.append(
        {
            "content_id": content_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "appeal",
            "status": "under_review",
            "reasoning": reasoning,
        }
    )

    return jsonify(
        {
            "content_id": content_id,
            "status": "under_review",
            "message": "Your appeal was received and is under review.",
        }
    )


if __name__ == "__main__":
    app.run(port=5000, debug=True)
