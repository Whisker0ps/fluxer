# Fluxer self-hosting (podman-compose, Rocky/RHEL) — Step-by-step

Assumptions:
- Running as user `fluxer`.
- `/home/fluxer` is empty.
- Rootless Podman + podman-compose are installed.
- Apache will reverse proxy to the Fluxer container.
- Fluxer source is checked out at `/home/fluxer/fluxer`.

## 1) Create directories
```bash
mkdir -p /home/fluxer/compose
mkdir -p /home/fluxer/config
mkdir -p /home/fluxer/data/fluxer
mkdir -p /home/fluxer/data/valkey
mkdir -p /home/fluxer/data/meilisearch
mkdir -p /home/fluxer/data/livekit
```

## 2) Build the Fluxer server image (multi-stage)
```bash
cd /home/fluxer/fluxer
podman build -f fluxer_server/Dockerfile -t fluxer-server:local .
```

Rebuild when you pull new code or change configs that affect the image:
```bash
cd /home/fluxer/fluxer
git pull
podman build --no-cache -f fluxer_server/Dockerfile -t fluxer-server:local .
```

Build notes:
- The Dockerfile installs Rust + wasm-pack for the web client build.
- The web client build requires `FLUXER_CONFIG` and generates i18n + emoji assets. If `config.json` is missing, the build copies the production template so the image still builds.
- The app build is domain-agnostic for static assets: script and asset URLs use a placeholder that the server replaces at runtime from your mounted config (`domain.base_domain`, etc.). You do not need to put your config or domain in the repo to build.
- Podman defaults to OCI format; HEALTHCHECK is ignored unless you build with `--format docker`.

Dockerignore exceptions used for build:
- `fluxer_app/src/data/emojis.json`
- `fluxer_app/scripts/build/**`

## 3) Create podman-compose file
Create `/home/fluxer/compose/podman-compose.yaml`:
```yaml
x-logging: &default-logging
  driver: json-file
  options:
    max-size: '10m'
    max-file: '5'

services:
  valkey:
    image: valkey/valkey:8.0.6-alpine
    container_name: valkey
    restart: unless-stopped
    command: ['valkey-server', '--appendonly', 'yes', '--save', '60', '1', '--loglevel', 'warning']
    volumes:
      - /home/fluxer/data/valkey:/data
    healthcheck:
      test: ['CMD', 'valkey-cli', 'ping']
      interval: 10s
      timeout: 5s
      retries: 5
    logging: *default-logging

  fluxer_server:
    image: ${FLUXER_SERVER_IMAGE:-fluxer-server:local}
    container_name: fluxer_server
    restart: unless-stopped
    init: true
    environment:
      FLUXER_CONFIG: /usr/src/app/config/config.json
      NODE_ENV: production
    ports:
      - '${FLUXER_HTTP_PORT:-8080}:8080'
    depends_on:
      valkey:
        condition: service_healthy
    volumes:
      - /home/fluxer/config:/usr/src/app/config:ro
      - /home/fluxer/data/fluxer:/usr/src/app/data
    healthcheck:
      test: ['CMD-SHELL', 'curl -fsS http://127.0.0.1:8080/_health || exit 1']
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 15s
    logging: *default-logging

  meilisearch:
    image: getmeili/meilisearch:v1.14
    container_name: meilisearch
    profiles: ['search']
    restart: unless-stopped
    environment:
      MEILI_ENV: production
      MEILI_MASTER_KEY: ${MEILI_MASTER_KEY:-}
      MEILI_DB_PATH: /meili_data
      MEILI_HTTP_ADDR: 0.0.0.0:7700
    ports:
      - '${MEILI_PORT:-7700}:7700'
    volumes:
      - /home/fluxer/data/meilisearch:/meili_data
    healthcheck:
      test: ['CMD-SHELL', 'curl -fsS http://127.0.0.1:7700/health || exit 1']
      interval: 15s
      timeout: 5s
      retries: 5
    logging: *default-logging

  livekit:
    image: livekit/livekit-server:v1.9.11
    container_name: livekit
    profiles: ['voice']
    restart: unless-stopped
    command: ['--config', '/etc/livekit/livekit.yaml']
    volumes:
      - /home/fluxer/config/livekit.yaml:/etc/livekit/livekit.yaml:ro
    ports:
      - '${LIVEKIT_PORT:-7880}:7880'
      - '7881:7881'
      - '3478:3478/udp'
      - '50000-50100:50000-50100/udp'
    healthcheck:
      test: ['CMD-SHELL', 'wget -qO- http://127.0.0.1:7880 || exit 1']
      interval: 15s
      timeout: 5s
      retries: 5
    logging: *default-logging
```

## 4) Create `.env` for optional services
Create `/home/fluxer/compose/.env`:
```bash
cat > /home/fluxer/compose/.env <<'EOF'
FLUXER_HTTP_PORT=8080
# Enable Meilisearch by setting a key and running with profile "search"
# MEILI_MASTER_KEY=replace_me
# Enable LiveKit by running with profile "voice"
# LIVEKIT_PORT=7880
EOF
```

## 5) Create config.json
Copy and edit `/home/fluxer/config/config.json` based on the production template.
Start with:
```bash
cat > /home/fluxer/config/config.json <<'EOF'
{
  "$schema": "../packages/config/src/ConfigSchema.json",
  "env": "production",
  "domain": {
    "base_domain": "chat.example.com",
    "public_scheme": "https",
    "public_port": 443
  },
  "database": {
    "backend": "sqlite",
    "sqlite_path": "./data/fluxer.db"
  },
  "internal": {
    "kv": "redis://valkey:6379/0"
  },
  "s3": {
    "access_key_id": "YOUR_S3_ACCESS_KEY",
    "secret_access_key": "YOUR_S3_SECRET_KEY",
    "endpoint": "http://127.0.0.1:8080/s3"
  },
  "services": {
    "server": {
      "port": 8080,
      "host": "0.0.0.0"
    },
    "media_proxy": {
      "secret_key": "GENERATE_A_64_CHAR_HEX_SECRET"
    },
    "admin": {
      "secret_key_base": "GENERATE_A_64_CHAR_HEX_SECRET",
      "oauth_client_secret": "GENERATE_A_64_CHAR_HEX_SECRET"
    },
    "marketing": {
      "enabled": true,
      "secret_key_base": "GENERATE_A_64_CHAR_HEX_SECRET"
    },
    "gateway": {
      "port": 8082,
      "admin_reload_secret": "GENERATE_A_64_CHAR_HEX_SECRET",
      "media_proxy_endpoint": "http://127.0.0.1:8080/media"
    },
    "nats": {
      "core_url": "nats://nats:4222",
      "jetstream_url": "nats://nats:4222",
      "auth_token": "GENERATE_A_NATS_AUTH_TOKEN"
    }
  },
  "auth": {
    "sudo_mode_secret": "GENERATE_A_64_CHAR_HEX_SECRET",
    "connection_initiation_secret": "GENERATE_A_64_CHAR_HEX_SECRET",
    "vapid": {
      "public_key": "YOUR_VAPID_PUBLIC_KEY",
      "private_key": "YOUR_VAPID_PRIVATE_KEY"
    }
  },
  "integrations": {
    "search": {
      "url": "http://meilisearch:7700",
      "api_key": "YOUR_MEILISEARCH_API_KEY"
    }
  }
}
EOF
```

Update these values before starting:
- `domain.base_domain`
- `services.*.secret_key*` and `auth.*` secrets
- `s3` credentials (and endpoint if using external S3)
- `services.nats` (see note below)

## 6) Start the stack
```bash
cd /home/fluxer/compose
podman-compose -f podman-compose.yaml up -d
```

Check health:
```bash
curl -fsS http://127.0.0.1:8080/_health
```

## Optional profiles
Enable Meilisearch:
```bash
cd /home/fluxer/compose
podman-compose --profile search up -d
```

Enable LiveKit:
```bash
cd /home/fluxer/compose
podman-compose --profile voice up -d
```

## Open questions (verify during Stage 5)
- NATS: config template expects NATS, but base compose does not include it.
- Gateway: confirm whether gateway runs inside fluxer_server or needs a separate service.
- S3: confirm internal S3 service is available at `/s3` in monolith mode.
