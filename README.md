# Netatmo Home Coach Prometheus Exporter

A Prometheus exporter for Netatmo Home Coach sensor data (temperature, CO2, humidity, noise, pressure, air quality index).

## Features

- OAuth 2.0 authentication with CSRF protection
- Automatic token refresh in the background
- Netatmo Home Coach sensor data retrieval via the Netatmo API
- Prometheus metrics export
- Built-in health check and exporter self-monitoring metrics
- Ready-to-use Docker Compose stack with Prometheus and Grafana

## Prerequisites

- Python 3.10+
- Netatmo account and API credentials
- Docker (optional)

## Installation

### Without Docker

1. Clone this repository:

    ```bash
    git clone https://github.com/guillaume-gambs/netatmo-aircare-exporter.git
    cd netatmo-aircare-exporter
    ```

1. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

1. Configure your Netatmo credentials as environment variables:

    ```bash
    cp .env.example .env
    # Edit .env with your credentials
    source .env
    export NETATMO_CLIENT_ID NETATMO_CLIENT_SECRET
    ```

1. Start the service:

    ```bash
    python netatmo_exporter.py
    ```

### With Docker (build from source)

1. Build the Docker image:

    ```sh
    docker build -t netatmo-aircare-exporter .
    ```

1. Run the container:

    ```sh
    docker run -d -p 8000:8000 \
        -e NETATMO_CLIENT_ID='your_client_id' \
        -e NETATMO_CLIENT_SECRET='your_client_secret' \
        --name netatmo-aircare-exporter netatmo-aircare-exporter
    ```

### With Docker from GHCR image

1. Run the container:

    ```sh
    docker run -d -p 8000:8000 \
        -e NETATMO_CLIENT_ID='your_client_id' \
        -e NETATMO_CLIENT_SECRET='your_client_secret' \
        --name netatmo-aircare-exporter ghcr.io/guillaume-gambs/netatmo-aircare-exporter:latest
    ```

### Full stack with Docker Compose

Start the exporter along with Prometheus and Grafana:

```bash
cp .env.example .env
# Edit .env with your credentials
docker compose up -d
```

This starts:
- **netatmo-exporter** on port `8000`
- **Prometheus** on port `9090` (pre-configured to scrape the exporter)
- **Grafana** on port `3000` (pre-provisioned with Prometheus datasource and dashboard)

### Optional environment variables

```bash
export NETATMO_EXPORTER_PORT=8000
export NETATMO_EXPORTER_REFRESH_INTERVAL=300
export NETATMO_API_URL="https://api.netatmo.com/api/gethomecoachsdata"
export NETATMO_AUTH_URL="https://api.netatmo.com/oauth2/authorize"
export NETATMO_TOKEN_URL="https://api.netatmo.com/oauth2/token"
export NETATMO_REDIRECT_URI="http://localhost:{PORT}/callback"
```

## Authentication

The exporter uses OAuth 2.0 to authenticate with the Netatmo API.

1. **Get your credentials**:
   - Create an account at [https://dev.netatmo.com/](https://dev.netatmo.com/)
   - Create a new application to obtain a `client_id` and `client_secret`

1. **Configure the application**:
   - Set `NETATMO_CLIENT_ID` and `NETATMO_CLIENT_SECRET` environment variables
   - You can use a `.env` file at the project root (make sure it is not committed)

1. **Authorize**:
   - Start the application — the full authorization URL is logged at startup
   - Open it in a browser or go to `http://localhost:8000`
   - Log in to your Netatmo account and authorize the application
   - You will be redirected back with an authorization code

1. **Token management**:
   - The application automatically exchanges the code for access and refresh tokens
   - Tokens are stored in memory (not persisted to disk)
   - The access token is refreshed automatically in the background before it expires

1. **Security**:
   - Never share your `client_id` and `client_secret`
   - Do not include credentials in source code or versioned configuration files
   - In production, use secret management solutions (Vault, Sealed Secrets, cloud secret managers)
   - Ensure the callback URL is secured and only accessible by your application

1. **Re-authorization**:
   - If the application is restarted, you will need to re-authorize
   - Repeat the authentication process by visiting `/`

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | OAuth2 authorization page |
| `/callback` | OAuth2 callback (automatic) |
| `/metrics` | Prometheus metrics |
| `/version` | Application version |
| `/health` | Health check (JSON) |

## For developers

### Automatic version update via git pre-commit hook

1. Create a `.git/hooks/pre-commit` file with the following content:

    ```bash
    #!/bin/sh
    python update_version.py
    git add version.py
    ```

1. Make it executable:

    ```bash
    chmod +x .git/hooks/pre-commit
    ```

## Troubleshooting

### The application does not start
- Check that `NETATMO_CLIENT_ID` and `NETATMO_CLIENT_SECRET` are set
- Check that the configured port is not already in use

### Metrics are empty
- Make sure you completed the OAuth2 authorization at `http://localhost:8000`
- Check the logs for authentication or API errors

### "Refresh token not found" error
- Authorization must be redone after each application restart
- Go to `http://localhost:8000` and follow the authorization link

### Authentication error after some time
- The application refreshes tokens automatically, but if the refresh token expires, re-authorize via `/`

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
