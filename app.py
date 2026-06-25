import uuid

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.errors import RateLimitExceeded
from flask_limiter.util import get_remote_address

from signals import llm_signal, combine_signals, label_selector

load_dotenv()

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)


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
def get_log():
    return jsonify({"logs": {}})


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

    s1 = llm_signal(text)
    confidence_score = combine_signals(s1, 0.0)
    label = label_selector(confidence_score)

    return jsonify(
        {
            "content_id": str(uuid.uuid4()),
            "confidence_score": round(confidence_score, 4),
            "label_key": label["label_key"],
            "label_text": label["label_text"],
            "label_detail": label["label_detail"],
        }
    )


@app.route("/appeal", methods=["POST"])
def appeal():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid or missing JSON payload."}), 400

    content_id = data.get("content_id")
    reasoning = data.get("reasoning")

    if not content_id or not reasoning:
        return jsonify(
            {"error": "Missing required fields: 'content_id' and 'reasoning'"}
        ), 400

    return jsonify(
        {
            "content_id": content_id,
            "status": "under_review",
            "message": "Your appeal was received and is under review.",
        }
    )


if __name__ == "__main__":
    app.run(port=5000, debug=True)
