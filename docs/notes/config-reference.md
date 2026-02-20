# Fluxer config reference notes (Stage 3 draft)

## Primary references
- `fluxer_docs/self_hosting/configuration.mdx` (full config schema reference)
- `config/config.production.template.json` (starting point)
- `config/config.dev.template.json` (dev overrides)

## Required root fields
From schema:
- `env`
- `domain`
- `database`
- `services`
- `auth`

## Monolith vs microservices
- `instance.deployment_mode` defaults to `monolith`.
- If `microservices`, you must provide `internal` and `services.app_proxy`.

## Database
- `database.backend`: `sqlite` or `cassandra`.
- `database.sqlite_path`: default `./data/fluxer.db`.
- Cassandra config required when backend is `cassandra`.

## Domain
- `domain.base_domain`, `domain.public_scheme`, `domain.public_port` derive public endpoints.

## S3
- `s3.access_key_id`, `s3.secret_access_key` required.
- `s3.endpoint` default `http://localhost:3900`.
- `s3.presigned_url_base` can be set to a public URL.

## Services (selected)
- `services.server`: host/port for main HTTP server.
- `services.gateway`: port for WS gateway.
- `services.media_proxy`: secret_key.
- `services.admin`: secret_key_base, oauth_client_secret.
- `services.marketing`: enabled, secret_key_base.
- `services.nats`: core_url, jetstream_url, auth_token.
- `services.s3`: data_dir and rate limiting (internal S3 service).

## Secrets to generate
From template:
- `services.media_proxy.secret_key`
- `services.admin.secret_key_base`
- `services.admin.oauth_client_secret`
- `services.gateway.admin_reload_secret`
- `services.nats.auth_token`
- `auth.sudo_mode_secret`
- `auth.connection_initiation_secret`
- `auth.vapid.public_key` / `auth.vapid.private_key`

## Notes
- The production template targets `sqlite` and points S3 to `http://127.0.0.1:8080/s3`.
- For podman-compose, bind-mount `~/config/config.json` to `/usr/src/app/config/config.json`.
- Keep `services.gateway.port` consistent with any reverse proxy WS routing.
