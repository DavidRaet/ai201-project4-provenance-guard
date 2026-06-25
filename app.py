import uuid

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/")
def home():
    return "Provenance Guard is running."


@app.route("/log", methods=["GET"])
def get_log():
    return jsonify({"logs": {}})


def submit():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid or missing JSON payload."}), 400

    text = data.get("text")
    creator_id = data.get("creator_id")

    if not text or not creator_id:
        return jsonify(
            {"error": "Missing required fields: 'text' and 'creator_id'"}
        ), 400

    return jsonify(
        {
            "content_id": str(uuid.uuid4()),
            "attribution": "uncertain",
            "confidence": 0.5,
            "label": "We're not sure who wrote this.",
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
