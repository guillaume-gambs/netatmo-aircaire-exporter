import os
import requests
from flask import Flask, Response, request, redirect
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Gauge, CollectorRegistry

app = Flask(__name__)

# Configuration
NETATMO_AUTH_URL = os.environ.get("NETATMO_AUTH_URL", "https://api.netatmo.com/oauth2/authorize")
NETATMO_TOKEN_URL = os.environ.get("NETATMO_TOKEN_URL", "https://api.netatmo.com/oauth2/token")
NETATMO_API_URL = os.environ.get("NETATMO_API_URL", "https://api.netatmo.com/api/gethomecoachsdata")
REFRESH_INTERVAL = int(os.environ.get("NETATMO_EXPORTER_REFRESH_INTERVAL", 300))
PORT = int(os.environ.get("NETATMO_EXPORTER_PORT", 8000))  # Port configurable avec 8000 comme valeur par défaut
REDIRECT_URI = os.environ.get("NETATMO_REDIRECT_URI", f"http://localhost:{PORT}/callback")
CLIENT_ID = os.environ["NETATMO_CLIENT_ID"]
CLIENT_SECRET = os.environ["NETATMO_CLIENT_SECRET"]
VERSION = "1.0.0"  # Définissez votre version ici

# Créer un registre Prometheus
registry = CollectorRegistry()

# Métriques Prometheus
netatmo_sensor_temperature_celsius = Gauge('netatmo_sensor_temperature_celsius', 'Temperature in Celsius', ['station_name', 'address_mac', 'city'], registry=registry)
netatmo_sensor_humidity_percent = Gauge('netatmo_sensor_humidity_percent', 'Relative humidity percentage', ['station_name', 'address_mac', 'city'], registry=registry)
netatmo_sensor_co2_ppm = Gauge('netatmo_sensor_co2_ppm', 'CO2 level in ppm', ['station_name', 'address_mac', 'city'], registry=registry)
netatmo_sensor_noise_db = Gauge('netatmo_sensor_noise_db', 'Noise level in dB', ['station_name', 'address_mac', 'city'], registry=registry)
netatmo_sensor_pressure_mb = Gauge('netatmo_sensor_pressure_mb', 'Atmospheric pressure in mbar', ['station_name', 'address_mac', 'city'], registry=registry)
netatmo_sensor_absolute_pressure_mb = Gauge('netatmo_sensor_absolute_pressure_mb', 'Absolute pressure in mbar', ['station_name', 'address_mac', 'city'], registry=registry)
netatmo_sensor_health_idx = Gauge('netatmo_sensor_health_idx', 'Health index', ['station_name', 'address_mac', 'city'], registry=registry)
netatmo_sensor_rf_signal_strength = Gauge('netatmo_sensor_rf_signal_strength', 'WiFi signal strength', ['station_name', 'address_mac', 'city'], registry=registry)

@app.route('/')
def auth():
    auth_params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'read_homecoach',
        'response_type': 'code',
    }
    auth_url = f"{NETATMO_AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in auth_params.items())}"
    return f'<a href="{auth_url}">Autoriser l\'application</a>'

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'redirect_uri': REDIRECT_URI,
    }
    response = requests.post(NETATMO_TOKEN_URL, data=token_data)
    tokens = response.json()

    os.environ["NETATMO_ACCESS_TOKEN"] = tokens['access_token']
    os.environ["NETATMO_REFRESH_TOKEN"] = tokens['refresh_token']

    return "Autorisation réussie ! Vous pouvez fermer cette fenêtre."

@app.route('/metrics')
def metrics():
    update_metrics()
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)

@app.route('/version')
def version():
    return f"Version: {VERSION}"

def get_access_token():
    if "NETATMO_REFRESH_TOKEN" not in os.environ:
        raise Exception("Refresh token non trouvé. Veuillez autoriser l'application d'abord.")

    auth_data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": os.environ["NETATMO_REFRESH_TOKEN"],
    }
    response = requests.post(NETATMO_TOKEN_URL, data=auth_data)
    if response.status_code != 200:
        raise Exception(f"Erreur d'authentification: {response.text}")
    token_data = response.json()
    os.environ["NETATMO_REFRESH_TOKEN"] = token_data["refresh_token"]
    return token_data["access_token"]

def get_netatmo_data(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(NETATMO_API_URL, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Erreur de récupération des données: {response.text}")
    return response.json()["body"]

def update_metrics():
    try:
        access_token = get_access_token()
        data = get_netatmo_data(access_token)

        for device in data["devices"]:
            labels = {
                'station_name': device['station_name'],
                'address_mac': device['_id'],
                'city': device['place']['city']
            }

            dashboard_data = device['dashboard_data']

            netatmo_sensor_temperature_celsius.labels(**labels).set(dashboard_data["Temperature"])
            netatmo_sensor_humidity_percent.labels(**labels).set(dashboard_data["Humidity"])
            netatmo_sensor_co2_ppm.labels(**labels).set(dashboard_data["CO2"])
            netatmo_sensor_noise_db.labels(**labels).set(dashboard_data["Noise"])
            netatmo_sensor_pressure_mb.labels(**labels).set(dashboard_data["Pressure"])
            netatmo_sensor_absolute_pressure_mb.labels(**labels).set(dashboard_data["AbsolutePressure"])
            netatmo_sensor_health_idx.labels(**labels).set(dashboard_data["health_idx"])
            netatmo_sensor_rf_signal_strength.labels(**labels).set(device["wifi_status"])

    except Exception as e:
        print(f"Erreur lors de la mise à jour des métriques : {e}")

if __name__ == "__main__":
    print(f"Démarrage du serveur sur le port {PORT}...")
    print(f"Intervalle de rafraîchissement des métriques : {REFRESH_INTERVAL} secondes")
    print(f"URL d'authentification Netatmo : {NETATMO_AUTH_URL}")
    print(f"URL de l'API Netatmo : {NETATMO_API_URL}")
    app.run(host='0.0.0.0', port=PORT)