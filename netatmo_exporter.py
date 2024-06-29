import os
import time
import requests
from prometheus_client import start_http_server, Gauge

# Configuration avec valeurs par défaut et possibilité de les surcharger via des variables d'environnement
NETATMO_AUTH_URL = os.environ.get("NETATMO_AUTH_URL", "https://api.netatmo.com/oauth2/token")
NETATMO_API_URL = os.environ.get("NETATMO_API_URL", "https://api.netatmo.com/api/gethomecoachsdata")
PORT = int(os.environ.get("NETATMO_EXPORTER_PORT", 8000))
REFRESH_INTERVAL = int(os.environ.get("NETATMO_EXPORTER_REFRESH_INTERVAL", 300)) # 5 minutes


# Métriques Prometheus avec labels
netatmo_sensor_temperature_celsius = Gauge('netatmo_sensor_temperature_celsius', 'Temperature in Celsius',
                    ['station_name', 'address_mac', 'city'])
netatmo_sensor_humidity_percent = Gauge('netatmo_sensor_humidity_percent', 'Relative humidity percentage',
                 ['station_name', 'address_mac', 'city'])
netatmo_sensor_co2_ppm = Gauge('netatmo_sensor_co2_ppm', 'CO2 level in ppm',
            ['station_name', 'address_mac', 'city'])
netatmo_sensor_noise_db = Gauge('netatmo_sensor_noise_db', 'Noise level in dB',
              ['station_name', 'address_mac', 'city'])
netatmo_sensor_pressure_mb = Gauge('netatmo_sensor_pressure_mb', 'Atmospheric pressure in mbar',
                 ['station_name', 'address_mac', 'city'])
netatmo_sensor_absolute_pressure_mb = Gauge('netatmo_sensor_absolute_pressure_mb', 'Absolute pressure in mbar',
                          ['station_name', 'address_mac', 'city'])
netatmo_sensor_health_idx = Gauge('netatmo_sensor_health_idx', 'Health index',
                   ['station_name', 'address_mac', 'city'])
netatmo_sensor_rf_signal_strength = Gauge('netatmo_sensor_rf_signal_strength', 'WiFi signal strength',
                    ['station_name', 'address_mac', 'city'])

def get_access_token():
    auth_data = {
        "grant_type": "refresh_token",
        "client_id": os.environ["NETATMO_CLIENT_ID"],
        "client_secret": os.environ["NETATMO_CLIENT_SECRET"],
        "refresh_token": os.environ["NETATMO_REFRESH_TOKEN"],
    }
    response = requests.post(NETATMO_AUTH_URL, data=auth_data)
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
    start_http_server(PORT)
    print(f"Serveur démarré sur le port {PORT}")
    print(f"Interval de rafraîchissement : {REFRESH_INTERVAL} secondes")
    print(f"URL d'authentification Netatmo : {NETATMO_AUTH_URL}")
    print(f"URL de l'API Netatmo : {NETATMO_API_URL}")

    while True:
        update_metrics()
        time.sleep(REFRESH_INTERVAL)