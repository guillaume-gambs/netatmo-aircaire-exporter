# Netatmo Home Coach Prometheus Exporter

Netatmo AirCare Exporter est un exportateur Prometheus pour les données des capteurs Netatmo Home Coach.

## Fonctionnalités

- Authentification oauth2 via redirection
- Récupération des données des capteurs Netatmo Home Coach via l'API Netatmo.
- Export des métriques vers Prometheus.

## Prérequis

- Python 3.7+
- Compte Netatmo et identifiants API
- Docker (optionnel)

## Installation

### Sans Docker

1. Clonez ce repository :

    ```bash
    git clone https://github.com/guillaume-gambs/netatmo-aircaire-exporter.git

    cd netatmo-aircaire-exporter
    ```

1. Installez les dépendances :

    ```bash
    pip install -r requirements.txt
    ```

1. Configurez vos identifiants Netatmo en tant que variables d'environnement :

    ```bash
    export NETATMO_CLIENT_ID='your_client_id'
    export NETATMO_CLIENT_SECRET='your_client_secret'
    export EXPORTER_PORT=8000
    ```

1. Démarrez le service :

    ```bash
    python netatmo_exporter.py
    ```

### Avec Docker et build des sources

1. Construisez l'image Docker :

    ```sh
    docker build -t netatmo-aircaire-exporter .
    ```

1. Exécutez le conteneur :

    ```sh
    docker run -d -p 8000:8000 \
        -e NETATMO_CLIENT_ID='your_client_id' \
        -e NETATMO_CLIENT_SECRET='your_client_secret' \
        --name my-netatmo-aircaire-exporter netatmo-aircaire-exporter
    ```

### Avec docker depuis l'image sur ghcr

1. Exécutez le conteneur :

    ```sh
    docker run -d -p 8000:8000 \
        -e NETATMO_CLIENT_ID='your_client_id' \
        -e NETATMO_CLIENT_SECRET='your_client_secret' \
        --name my-netatmo-aircaire-exporter **ghcr**.io/guillaume-gambs/netatmo-aircaire-exporter:latest
    ```

### Aller plus loin

Il existe des variable optionnel

```bash
export NETATMO_EXPORTER_PORT=8000
export NETATMO_EXPORTER_REFRESH_INTERVAL=300
export NETATMO_API_URL="https://api.netatmo.com/api/gethomecoachsdata"
export NETATMO_AUTH_URL="https://api.netatmo.com/oauth2/authorize"
export NETATMO_TOKEN_URL="https://api.netatmo.com/oauth2/token"
export NETATMO_REDIRECT_URI="http://localhost:{PORT}/callback"
```

### Authentification

Le Netatmo AirCare Exporter utilise le protocole OAuth 2.0 pour s'authentifier auprès de l'API Netatmo. Voici les étapes pour configurer et utiliser l'authentification :

1. **Obtention des identifiants** :
   - Créez un compte sur [https://dev.netatmo.com/](https://dev.netatmo.com/)
   - Créez une nouvelle application pour obtenir un `client_id` et un `client_secret`

1. **Configuration de l'application** :
   - Définissez les variables d'environnement `NETATMO_CLIENT_ID` et `NETATMO_CLIENT_SECRET` avec vos identifiants
   - Vous pouvez les définir dans un fichier `.env` à la racine du projet (assurez-vous de ne pas le committer)

1. **Processus d'authentification** :
   - Lancez l'application et accédez à `http://127.0.0.1:8000`
   - Cliquez sur le lien d'autorisation qui vous redirigera vers la page d'authentification Netatmo
   - Connectez-vous à votre compte Netatmo et autorisez l'application
   - Vous serez redirigé vers l'application avec un code d'autorisation

1. **Gestion des tokens** :
   - L'application échangera automatiquement le code d'autorisation contre un access token et un refresh token
   - Ces tokens seront stockés temporairement dans les variables d'environnement /!\
   - L'application rafraîchira automatiquement l'access token lorsque nécessaire

1. **Sécurité** :
   - Ne partagez jamais votre `client_id` et `client_secret`
   - N'incluez pas ces informations directement dans le code source ou les fichiers de configuration versionnés
   - En production, utilisez des solutions de gestion de secrets comme Vault, Sealed secret ou les secrets managers des plateformes cloud
   - Assurez-vous que l'URL de callback est sécurisée et accessible uniquement par votre application

1. **Renouvellement de l'autorisation** :
   - Si vous redémarrez l'application, vous devrez peut-être réautoriser l'accès
   - Répétez le processus d'authentification si nécessaire

En suivant ces étapes, vous assurez une authentification sécurisée pour accéder aux données de vos capteurs Netatmo via l'API.
N'oubliez pas de consulter régulièrement la documentation de l'API Netatmo pour toute mise à jour concernant le processus d'authentification.

## Pour les developeurs

### Mise à jour du fichier de version.py via git hook pre-commit

1. Créez un fichier `.git/hooks/pre-commit` (sans extension) avec le contenu suivant :

    ```bash
    #!/bin/sh
    python update_version.py
    git add version.py
    ```

1. Rendez ce fichier exécutable :

    ```bash
    chmod +x .git/hooks/pre-commit
    ```

## Utilisation

Accédez aux métriques via http://localhost:8000/metrics


## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](./LICENSE) pour plus de détails.
