import os
import logging
import secrets
import time
import threading
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask import Flask, Response, request, jsonify
from markupsafe import escape
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Gauge, Counter, CollectorRegistry

from version import __version__

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
NETATMO_AUTH_URL = os.environ.get("NETATMO_AUTH_URL", "https://api.netatmo.com/oauth2/authorize")
NETATMO_TOKEN_URL = os.environ.get("NETATMO_TOKEN_URL", "https://api.netatmo.com/oauth2/token")
NETATMO_API_URL = os.environ.get("NETATMO_API_URL", "https://api.netatmo.com/api/gethomecoachsdata")
REFRESH_INTERVAL = int(os.environ.get("NETATMO_EXPORTER_REFRESH_INTERVAL", 300))
PORT = int(os.environ.get("NETATMO_EXPORTER_PORT", 8000))
REDIRECT_URI = os.environ.get("NETATMO_REDIRECT_URI", f"http://localhost:{PORT}/callback")
CLIENT_ID = os.environ["NETATMO_CLIENT_ID"]
CLIENT_SECRET = os.environ["NETATMO_CLIENT_SECRET"]

# Token storage (in-memory, not in environment variables)
_token_store = {
    "access_token": None,
    "refresh_token": None,
    "expires_at": 0,
}

# OAuth2 CSRF state
_oauth_state = None

# HTTP session with retry
http_session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
http_session.mount("https://", HTTPAdapter(max_retries=retries))

# Créer un registre Prometheus
registry = CollectorRegistry()

# Métriques Prometheus — capteurs
netatmo_sensor_temperature_celsius = Gauge('netatmo_sensor_temperature_celsius', 'Temperature in Celsius', ['station_name', 'address_mac', 'city'], registry=registry)
netatmo_sensor_humidity_percent = Gauge('netatmo_sensor_humidity_percent', 'Relative humidity percentage', ['station_name', 'address_mac', 'city'], registry=registry)
netatmo_sensor_co2_ppm = Gauge('netatmo_sensor_co2_ppm', 'CO2 level in ppm', ['station_name', 'address_mac', 'city'], registry=registry)
netatmo_sensor_noise_db = Gauge('netatmo_sensor_noise_db', 'Noise level in dB', ['station_name', 'address_mac', 'city'], registry=registry)
netatmo_sensor_pressure_mb = Gauge('netatmo_sensor_pressure_mb', 'Atmospheric pressure in mbar', ['station_name', 'address_mac', 'city'], registry=registry)
netatmo_sensor_absolute_pressure_mb = Gauge('netatmo_sensor_absolute_pressure_mb', 'Absolute pressure in mbar', ['station_name', 'address_mac', 'city'], registry=registry)
netatmo_sensor_health_idx = Gauge('netatmo_sensor_health_idx', 'Health index', ['station_name', 'address_mac', 'city'], registry=registry)
netatmo_sensor_rf_signal_strength = Gauge('netatmo_sensor_rf_signal_strength', 'WiFi signal strength', ['station_name', 'address_mac', 'city'], registry=registry)

# Métriques d'auto-monitoring
netatmo_exporter_scrape_errors_total = Counter('netatmo_exporter_scrape_errors_total', 'Total number of scrape errors', registry=registry)
netatmo_exporter_last_scrape_duration_seconds = Gauge('netatmo_exporter_last_scrape_duration_seconds', 'Duration of the last scrape in seconds', registry=registry)
netatmo_exporter_up = Gauge('netatmo_exporter_up', 'Whether the last scrape was successful (1=ok, 0=error)', registry=registry)
netatmo_exporter_auth_needed = Gauge('netatmo_exporter_auth_needed', 'Whether OAuth2 authorization is needed (1=needed, 0=authorized)', registry=registry)
netatmo_exporter_token_expires_at = Gauge('netatmo_exporter_token_expires_at', 'Unix timestamp when the access token expires (0=no token)', registry=registry)
netatmo_exporter_token_ttl_seconds = Gauge('netatmo_exporter_token_ttl_seconds', 'Seconds remaining before access token expires', registry=registry)

# Initialize auth_needed to 1 (no token yet at startup)
netatmo_exporter_auth_needed.set(1)


@app.route('/')
def auth():
    global _oauth_state
    if not _oauth_state:
        _oauth_state = secrets.token_urlsafe(32)
    auth_params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'read_homecoach',
        'response_type': 'code',
        'state': _oauth_state,
    }
    auth_url = f"{NETATMO_AUTH_URL}?{urlencode(auth_params)}"
    safe_url = escape(auth_url)
    return f'<a href="{safe_url}">Autoriser l\'application</a>'


@app.route('/callback')
def callback():
    global _oauth_state
    code = request.args.get('code')
    state = request.args.get('state')

    if not code:
        logger.warning("Callback appelé sans paramètre 'code'")
        return "Erreur : paramètre 'code' manquant.", 400

    if not state or state != _oauth_state:
        logger.warning("Callback avec state OAuth2 invalide (possible CSRF)")
        return "Erreur : state invalide.", 403

    _oauth_state = None

    token_data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'redirect_uri': REDIRECT_URI,
    }
    response = http_session.post(NETATMO_TOKEN_URL, data=token_data)

    if response.status_code != 200:
        logger.error("Échec de l'échange du code d'autorisation : %s", response.text)
        return "Erreur lors de l'échange du code d'autorisation.", 500

    tokens = response.json()
    _token_store["access_token"] = tokens['access_token']
    _token_store["refresh_token"] = tokens['refresh_token']
    _token_store["expires_at"] = time.time() + tokens.get('expires_in', 10800)

    netatmo_exporter_auth_needed.set(0)
    netatmo_exporter_token_expires_at.set(_token_store["expires_at"])
    netatmo_exporter_token_ttl_seconds.set(tokens.get('expires_in', 10800))

    logger.info("Autorisation réussie, token expire dans %d secondes", tokens.get('expires_in', 10800))
    return "Autorisation réussie ! Vous pouvez fermer cette fenêtre."


@app.route('/metrics')
def metrics():
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)


@app.route('/version')
def version():
    return f"Version: {__version__}"


@app.route('/health')
def health():
    return jsonify({"status": "ok", "version": __version__})


def get_access_token():
    if not _token_store["refresh_token"]:
        netatmo_exporter_auth_needed.set(1)
        raise Exception("Refresh token non trouvé. Veuillez autoriser l'application d'abord.")

    auth_data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": _token_store["refresh_token"],
    }
    response = http_session.post(NETATMO_TOKEN_URL, data=auth_data)
    if response.status_code != 200:
        netatmo_exporter_auth_needed.set(1)
        raise Exception(f"Erreur d'authentification: {response.text}")
    token_data = response.json()
    _token_store["access_token"] = token_data["access_token"]
    _token_store["refresh_token"] = token_data["refresh_token"]
    _token_store["expires_at"] = time.time() + token_data.get('expires_in', 10800)

    netatmo_exporter_auth_needed.set(0)
    netatmo_exporter_token_expires_at.set(_token_store["expires_at"])
    netatmo_exporter_token_ttl_seconds.set(token_data.get('expires_in', 10800))
    logger.info("Token rafraîchi, expire dans %d secondes", token_data.get('expires_in', 10800))

    return token_data["access_token"]


def get_netatmo_data(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = http_session.get(NETATMO_API_URL, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Erreur de récupération des données: {response.text}")
    return response.json()["body"]


def update_metrics():
    start_time = time.monotonic()
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

        netatmo_exporter_up.set(1)
        logger.info("Métriques mises à jour avec succès")

    except Exception as e:
        netatmo_exporter_up.set(0)
        netatmo_exporter_scrape_errors_total.inc()
        logger.error("Erreur lors de la mise à jour des métriques : %s", e)
    finally:
        duration = time.monotonic() - start_time
        netatmo_exporter_last_scrape_duration_seconds.set(duration)


def background_refresh():
    while True:
        if _token_store["refresh_token"]:
            logger.info("Rafraîchissement des métriques en arrière-plan...")
            update_metrics()
        time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    # Générer le state OAuth2 au démarrage pour pouvoir loguer l'URL complète
    _oauth_state = secrets.token_urlsafe(32)
    auth_params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'read_homecoach',
        'response_type': 'code',
        'state': _oauth_state,
    }
    auth_url = f"{NETATMO_AUTH_URL}?{urlencode(auth_params)}"

    logger.info("Démarrage du serveur sur le port %d...", PORT)
    logger.info("Intervalle de rafraîchissement : %d secondes", REFRESH_INTERVAL)
    logger.info("URL d'authentification Netatmo : %s", NETATMO_AUTH_URL)
    logger.info("URL de l'API Netatmo : %s", NETATMO_API_URL)
    logger.info("Autorisez l'application ici : %s", auth_url)
    logger.info("Version : %s", __version__)

    refresh_thread = threading.Thread(target=background_refresh, daemon=True)
    refresh_thread.start()

    app.run(host='0.0.0.0', port=PORT)