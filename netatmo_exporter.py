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
temperature = Gauge('netatmo_temperature', 'Temperature in Celsius',
                    ['station_name', 'address_mac', 'city'])
humidity = Gauge('netatmo_humidity', 'Relative humidity percentage',
                 ['station_name', 'address_mac', 'city'])
co2 = Gauge('netatmo_co2', 'CO2 level in ppm',
            ['station_name', 'address_mac', 'city'])
noise = Gauge('netatmo_noise', 'Noise level in dB',
              ['station_name', 'address_mac', 'city'])
pressure = Gauge('netatmo_pressure', 'Atmospheric pressure in mbar',
                 ['station_name', 'address_mac', 'city'])
absolute_pressure = Gauge('netatmo_absolute_pressure', 'Absolute pressure in mbar',
                          ['station_name', 'address_mac', 'city'])
health_idx = Gauge('netatmo_health_idx', 'Health index',
                   ['station_name', 'address_mac', 'city'])
wifi_status = Gauge('netatmo_wifi_status', 'WiFi signal strength',
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

            temperature.labels(**labels).set(dashboard_data["Temperature"])
            humidity.labels(**labels).set(dashboard_data["Humidity"])
            co2.labels(**labels).set(dashboard_data["CO2"])
            noise.labels(**labels).set(dashboard_data["Noise"])
            pressure.labels(**labels).set(dashboard_data["Pressure"])
            absolute_pressure.labels(**labels).set(dashboard_data["AbsolutePressure"])
            health_idx.labels(**labels).set(dashboard_data["health_idx"])
            wifi_status.labels(**labels).set(device["wifi_status"])

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