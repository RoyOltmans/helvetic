import os
import json
import struct
from datetime import datetime
from pathlib import Path
from threading import Lock
from bottle import request, response
from crcmod.predefined import mkCrcFun
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(os.getenv('HEL_DATA_DIR', 'data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)
USERS_FILE = DATA_DIR / 'users.json'
MEASUREMENTS_FILE = DATA_DIR / 'measurements.json'
data_lock = Lock()

GENDERS = {'f': 0, 'm': 2}
crc16xmodem = mkCrcFun('xmodem')

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

def get_user_by_id(uid):
    users = load_json(USERS_FILE, [])
    for user in users:
        if str(user.get('id')) == str(uid):
            return user
    return None

def register_aria_routes(app):
    @app.post('/scale/upload')
    def upload():
        log('headers = %r', dict(request.headers))
        response.set_header('Content-Type', 'application/octet-stream;charset=UTF-8')
        body = request.body.read()

        if len(body) < 30:
            log("Not enough bytes for protocol header!")
            response.status = 400
            return "ERR"
        proto_ver, battery_pc, mac, authcode = struct.unpack('<LL6s16s', body[:30])
        body = body[30:]
        log('upload: %d / %d%% / %r / %r', proto_ver, battery_pc, mac, authcode)

        if len(body) < 16:
            log("Not enough bytes for fw header!")
            response.status = 400
            return "ERR"
        fw_ver, unknown2, ts, measurement_count = struct.unpack('<LLLL', body[:16])
        body = body[16:]
        log('fw = %d / u33 = %d / ts = %d / count = %d', fw_ver, unknown2, ts, measurement_count)

        measurements = load_json(MEASUREMENTS_FILE, [])
        first_measurement = None
        all_weights = []
        for x in range(measurement_count):
            if len(body) < 32:
                log('oops, not enough bytes to decode measurement!')
                break
            id2, imp, weight, scale_ts, uid, fat1, covar, fat2 = struct.unpack('<LLLLLLLL', body[:32])
            w = round(weight / 1000.0, 3)
            all_weights.append(w)
            if first_measurement is None:
                first_measurement = {
                    "user_id": uid,
                    "weight": w,
                    "body_fat": fat1,
                    "timestamp": datetime.now().isoformat(),
                    "is_guest": get_user_by_id(uid) is None,
                    "raw": {
                        "id2": id2,
                        "imp": imp,
                        "covar": covar,
                        "fat2": fat2,
                        "proto_ts": scale_ts
                    }
                }
            log('id2 = %d / imp = %d / weight = %.3f / ts = %d', id2, imp, w, scale_ts)
            log('uid = %d / fat1 = %d / covar = %d / fat2 = %d', uid, fat1, covar, fat2)
            body = body[32:]
        log("All weights in upload: %r", all_weights)

        # Store only the first measurement!
        if first_measurement:
            measurements.append(first_measurement)
            save_json(MEASUREMENTS_FILE, measurements)

            # Dynamically update min/max tolerance for this user for next sync
            TOLERANCE_GRAMS = 500  # ±0.5kg
            if not first_measurement["is_guest"]:
                users = load_json(USERS_FILE, [])
                for user in users:
                    if str(user.get("id")) == str(first_measurement["user_id"]):
                        w = int(round(first_measurement["weight"] * 1000))
                        user["min_tolerance"] = w - TOLERANCE_GRAMS
                        user["max_tolerance"] = w + TOLERANCE_GRAMS
                        log('Updated user %s min/max_tolerance to [%d, %d]', user["name"], user["min_tolerance"], user["max_tolerance"])
                        break
                save_json(USERS_FILE, users)

        log('checksum = %r', body)

        # --- Multi-user profile protocol reply ---
        users = load_json(USERS_FILE, [])
        if not users:
            users = [{
                "name": os.getenv("HEL_USER_DEFAULT_NAME", "EXAMPLE"),
                "height": int(os.getenv("HEL_USER_DEFAULT_HEIGHT", "1900")),
                "birthyear": int(os.getenv("HEL_USER_DEFAULT_BIRTHYEAR", "1970")),
                "gender": os.getenv("HEL_USER_DEFAULT_GENDER", "m"),
                "min_tolerance": int(os.getenv('HEL_MIN_TOLERANCE', 89000)),
                "max_tolerance": int(os.getenv('HEL_MAX_TOLERANCE', 97000)),
            }]

        user_count = len(users)
        profiles = b''

        for idx, user in enumerate(users, start=1):
            age = datetime.now().year - int(user.get("birthyear", 1970))
            gender = GENDERS.get(user.get("gender", "m")[:1].lower(), 0x34)
            height = int(user.get("height", 1900))
            name = user.get("name", "EXAMPLE")[:20].upper().ljust(20)
            min_tol = int(user.get("min_tolerance", os.getenv('HEL_MIN_TOLERANCE', 89000)))
            max_tol = int(user.get("max_tolerance", os.getenv('HEL_MAX_TOLERANCE', 97000)))
            profiles += struct.pack('<LBBBLL16x20sLLLBLLLLLLLLL',
                int(datetime.now().timestamp()),
                0x02,     # units (kg)
                0x32,     # status: "configured"
                0x01,     # unknown
                user_count,
                idx,      # user index
                name.encode("ascii"),
                min_tol,
                max_tol,
                age,
                gender,
                height,
                0, 0, 0, 0, 0, 0, 3, 0,
            )

        packet_size = 0x19 + (user_count * 0x4d)
        full_packet = struct.pack(f'<{len(profiles)}sHH', profiles, crc16xmodem(profiles), packet_size)
        return full_packet

    @app.get('/scale/register')
    def register():
        log('register query = %r', dict(request.query))
        return ''

    @app.get('/scale/validate')
    def validate():
        log('validate query = %r', dict(request.query))
        return 'T'
