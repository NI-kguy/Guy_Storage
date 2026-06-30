"""
Table Tennis Tournament - Local Server
Run: python server.py
Then open: http://localhost:5000  (or http://<your-ip>:5000 from other devices)
"""

import json
import os
import socket
from flask import Flask, send_file, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = os.path.join(os.path.dirname(__file__), "tt_data.json")
HTML_FILE = os.path.join(os.path.dirname(__file__), "table_tennis_tournament.html")


def read_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def write_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Serve HTML ────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_file(HTML_FILE)


# ── Get current data ──────────────────────────────────────────────────
@app.route("/api/data", methods=["GET"])
def get_data():
    return jsonify(read_data())


# ── Save data ─────────────────────────────────────────────────────────
@app.route("/api/data", methods=["POST"])
def post_data():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid payload"}), 400
    write_data(payload)
    return jsonify({"ok": True})


# ── Clear data ────────────────────────────────────────────────────────
@app.route("/api/clear", methods=["POST"])
def clear_data():
    write_data({})
    return jsonify({"ok": True})


# ── Print local IP so the user knows what to share ───────────────────
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


if __name__ == "__main__":
    ip = get_local_ip()
    print("=" * 52)
    print("  Table Tennis Tournament Server")
    print("=" * 52)
    print(f"  This laptop : http://localhost:5000")
    print(f"  Other devices: http://{ip}:5000")
    print("=" * 52)
    print("  Press Ctrl+C to stop the server")
    print()
    app.run(host="0.0.0.0", port=5000, debug=False)
