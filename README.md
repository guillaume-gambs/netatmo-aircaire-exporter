# Netatmo Home Coach Prometheus Exporter

Ce projet est un exportateur Prometheus pour les données du capteur Netatmo Home Coach. Il récupère les données via l'API Netatmo et les expose dans un format compatible avec Prometheus.

## Prérequis

- Python 3.7+
- Compte Netatmo et identifiants API

## Installation

1. Clonez ce repository :

```bash
git clone https://github.com/votre-nom-utilisateur/netatmo-prometheus-exporter.git
cd netatmo-prometheus-exporter
```

2. Installez les dépendances :

```bash
pip install -r requirements.txt
```

3. Configurez vos identifiants Netatmo en tant que variables d'environnement :

```bash
export NETATMO_CLIENT_ID=votre_client_id
export NETATMO_CLIENT_SECRET=votre_client_secret
export NETATMO_REFRESH_TOKEN=votre_refresh_token
```

Variable optionnel
```bash
export NETATMO_EXPORTER_PORT=9000
export NETATMO_EXPORTER_REFRESH_INTERVAL=600
export NETATMO_AUTH_URL="https://custom-auth-url.com"
export NETATMO_API_URL="https://custom-api-url.com"
```

Pour obtenir un refresh_token, vous devrez d'abord autoriser votre application via le flux OAuth 2.0. Consultez la documentation Netatmo pour plus de détails sur ce processus.


# Pour les developeurs

il faut mettre dans `.git/hooks/pre-commit`

```bash
#!/bin/sh
python update_version.py
git add version.py
```

## Utilisation

Lancez l'exporteur :

```bash
python netatmo_exporter.py
```

L'exportateur sera accessible à `http://localhost:8000/metrics`.

## Docker

Pour exécuter l'exportateur dans un conteneur Docker :

1. Construisez l'image :

```bash
docker build -t netatmo-aircaire-exporter .
```

1. Lancez le conteneur :

```bash
docker run -d --name netatmo-aircaire-exporter -p 8000:8000 \
-e NETATMO_CLIENT_ID="votre_client_id" \
-e NETATMO_CLIENT_SECRET="votre_client_secret" \
-e NETATMO_REFRESH_TOKEN="votre_refresh_token" \
netatmo-aircaire-exporter:latest
```

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.
