# Fluxer self-hosting architecture notes (Stage 1)

## Component map (repo)
- fluxer_server: TypeScript umbrella service for self-hosters; composes multiple backend services.
- fluxer_api: TypeScript HTTP API service (Hono).
- fluxer_gateway: Erlang/OTP WebSocket gateway (real-time messaging/presence).
- fluxer_relay: Erlang relay service.
- fluxer_relay_directory: TypeScript service for relay discovery/directory.
- fluxer_media_proxy: TypeScript media proxy service.
- fluxer_app_proxy: TypeScript app proxy for serving/proxying the web client.
- fluxer_admin: Admin UI/service.
- fluxer_app: React web client (Rspack build; includes Rust crates).
- fluxer_static: Static CDN payload (avatars, emojis, fonts, web icons, MediaPipe libs).
- fluxer_docs: Docs site (Mint), includes self-hosting section skeletons.
- fluxer_devops: Deployment helpers and service configs (NATS, Valkey, etc.).
- packages/*: Shared libraries (config, schema, auth, queue, telemetry, etc.).

## External services and dependencies (from repo configs)
- Database: SQLite (dev/single-node) or Cassandra (prod).
- KV/Cache: Valkey (Redis-compatible) via internal.kv config.
- Message bus: NATS (core + jetstream URLs in config).
- Search: Meilisearch (optional profile in compose).
- Voice: LiveKit (optional profile in compose).
- Object storage: S3-compatible endpoint (config requires keys and endpoint).

## Default ports and network hints (from templates/compose)
- fluxer_server HTTP: 8080 (services.server.port in config template).
- fluxer_gateway: 8082 (services.gateway.port in config template).
- Valkey: 6379 (compose internal service).
- Meilisearch: 7700 (compose profile: search).
- LiveKit: 7880 (HTTP), 7881 (RTC), 3478/udp (STUN/TURN), 50000-50100/udp (media).

## Existing self-hosting docs and gaps
- fluxer_docs/self_hosting/quickstart.mdx: TBD.
- fluxer_docs/self_hosting/voice.mdx: TBD.
- fluxer_docs/self_hosting/configuration.mdx: auto-generated config reference (present).
- README points to external self-hosting guide, but local docs are incomplete.

## Open questions to resolve in later stages
- Which services are required for a minimal production instance (server + gateway + relay + media proxy + app proxy + admin)?
- Exact inter-service routing and ports (gateway <-> server, media proxy <-> server, relay topology).
- Which components are bundled in fluxer_server vs run separately in production.
- Required storage backends (S3 local vs external; Cassandra vs SQLite viability).
- Required background/worker processes (if any) and how they are launched.
