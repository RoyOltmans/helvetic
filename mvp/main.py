import os
from bottle import Bottle, run
from dotenv import load_dotenv
from api_service import register_api_routes
from aria_service import register_aria_routes

load_dotenv()

PORT = int(os.getenv('HEL_PORT', 8000))
HOST = os.getenv('HEL_HOST', '0.0.0.0')

app = Bottle()
register_api_routes(app)
register_aria_routes(app)

@app.get('/')
def index():
    return (
        "Helvetic Unified API\n\n"
        "/users [GET, POST]\n"
        "/users/<id> [PUT, DELETE]\n"
        "/measurements [GET, POST]\n"
        "/measurements/latest?user_id=... [GET]\n"
        "/scale/register, /scale/validate, /scale/upload [Scale protocol]\n"
    )

if __name__ == '__main__':
    print(f'helvetic unified API running on http://{HOST}:{PORT}')
    run(app, host=HOST, port=PORT, debug=True, reloader=True)
