import os
from bottle import request, response
import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(os.getenv('HEL_DATA_DIR', 'data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)
USERS_FILE = DATA_DIR / 'users.json'
MEASUREMENTS_FILE = DATA_DIR / 'measurements.json'
data_lock = Lock()

GENDERS = {'f': 0, 'm': 2}

def log(msg, *args):
    print(datetime.now().isoformat() + ": " + (msg % args if args else msg))

def load_json(file, default):
    with data_lock:
        if not file.exists():
            return default
        try:
            with file.open("r") as f:
                return json.load(f)
        except Exception:
            return default

def save_json(file, data):
    with data_lock:
        with file.open("w") as f:
            json.dump(data, f, indent=2)

def new_user_id(users):
    if not users:
        return 1
    return max(u["id"] for u in users) + 1

def new_measurement_id(measurements):
    if not measurements:
        return 1
    return max((m.get("id", 0) for m in measurements), default=0) + 1

def get_user_by_id(uid):
    users = load_json(USERS_FILE, [])
    for user in users:
        if str(user['id']) == str(uid):
            return user
    return None

# ---- REST API endpoints ----
def register_api_routes(app):
    @app.get("/users")
    def get_users():
        users = load_json(USERS_FILE, [])
        response.content_type = "application/json"
        return json.dumps(users)

    @app.post("/users")
    def add_user():
        users = load_json(USERS_FILE, [])
        data = request.json
        if not data or "name" not in data:
            response.status = 400
            return {"error": "Missing required field: name"}
        user = {
            "id": new_user_id(users),
            "name": data["name"],
            "birthyear": data.get("birthyear"),
            "gender": data.get("gender"),
            "height": data.get("height"),
            "created": datetime.now().isoformat()
        }
        users.append(user)
        save_json(USERS_FILE, users)
        response.status = 201
        return user

    @app.put("/users/<uid:int>")
    def update_user(uid):
        users = load_json(USERS_FILE, [])
        user = next((u for u in users if u["id"] == uid), None)
        if not user:
            response.status = 404
            return {"error": "User not found"}
        data = request.json or {}
        for k in ["name", "birthyear", "gender", "height"]:
            if k in data:
                user[k] = data[k]
        save_json(USERS_FILE, users)
        return user

    @app.delete("/users/<uid:int>")
    def delete_user(uid):
        users = load_json(USERS_FILE, [])
        users = [u for u in users if u["id"] != uid]
        save_json(USERS_FILE, users)
        response.status = 204
        return ""

    @app.get("/measurements")
    def get_measurements():
        measurements = load_json(MEASUREMENTS_FILE, [])
        user_id = request.query.get("user_id")
        if user_id:
            measurements = [m for m in measurements if str(m.get("user_id")) == str(user_id)]
        response.content_type = "application/json"
        return json.dumps(measurements)

    @app.post("/measurements")
    def add_measurement():
        measurements = load_json(MEASUREMENTS_FILE, [])
        data = request.json
        required = {"user_id", "weight"}
        if not data or not required.issubset(data.keys()):
            response.status = 400
            return {"error": "Missing required fields: user_id, weight"}
        entry = {
            "id": new_measurement_id(measurements),
            "user_id": data["user_id"],
            "weight": data["weight"],
            "body_fat": data.get("body_fat"),
            "timestamp": data.get("timestamp") or datetime.now().isoformat()
        }
        measurements.append(entry)
        save_json(MEASUREMENTS_FILE, measurements)
        response.status = 201
        return entry

    @app.get("/measurements/latest")
    def latest_measurement():
        measurements = load_json(MEASUREMENTS_FILE, [])
        user_id = request.query.get("user_id")
        if not user_id:
            response.status = 400
            return {"error": "Missing user_id"}
        user_measurements = [m for m in measurements if str(m.get("user_id")) == str(user_id)]
        if not user_measurements:
            response.status = 404
            return {"error": "No measurements found for user"}
        latest = max(user_measurements, key=lambda m: m["timestamp"])
        response.content_type = "application/json"
        return json.dumps(latest)
