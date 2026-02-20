# Fluxer build/tooling notes (Stage 1)

## Toolchain and package managers
- Node.js: >= 24 (root .nvmrc is 24; fluxer_server engines >= 24.0.0).
- pnpm: 10.29.3 (root package.json packageManager).
- Turborepo: used for build/lint/test orchestration (turbo.json).
- TypeScript runtime: tsx used for dev/start scripts in services.
- TypeScript native preview: tsgo used for typecheck in services (via @typescript/native-preview).
- Biome: lint/format (biome.json + root devDependencies).

## Language-specific toolchains
- Rust: toolchain 1.93.0 (fluxer_app/rust-toolchain.toml) for Rust crates in fluxer_app.
- Erlang/OTP + rebar3: required for fluxer_gateway and fluxer_relay (rebar.config present).

## Build/deployment pathways detected
- Docker/Compose: compose.yaml provides a production-ish baseline (fluxer_server + valkey, optional meilisearch/livekit).
- Nix/devenv: README says development is supported via devenv only.

## Known scripts (root)
- build: turbo run build
- dev: scripts/run_dev.sh (devenv-based)
- dev:docs: mint dev in fluxer_docs
- docs:generate: config + API resources + media proxy docs

## Open questions to resolve in later stages
- Required versions for Erlang/OTP and rebar3.
- Whether tsgo is required for production builds or only typecheck.
- Exact build steps for fluxer_gateway / fluxer_relay / fluxer_relay_directory in production.
- Whether fluxer_app and fluxer_admin are built separately or through fluxer_server.
