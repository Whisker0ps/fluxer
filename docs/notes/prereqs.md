# Fluxer self-hosting prerequisites (Stage 2 draft)

## Target environment
- Linux server with systemd (tested target for docs).
- Dedicated service user (e.g., `fluxer`) and home directory for configs and data.
- Container runtime: Podman + podman-compose (rootless) OR Docker + Compose.
- Known deployment OS: Rocky Linux 9.7 (RHEL 9 family).

## Hardware guidance (small deployment)
Assumption: 1-3 communities, <100 channels each, <100 users each.
- 4+ vCPU, 8-16 GB RAM, SSD/NVMe storage.
- Your server (128 GB RAM, NVMe) is more than sufficient for this size.

## Storage
- Prefer bind mounts for persistent data.
- Separate directories for:
  - `config/` (config.json, livekit.yaml)
  - `data/` (fluxer_server data)
  - `valkey/` (KV store)
  - `meilisearch/` (search index, optional)
  - `livekit/` (voice config + state, optional)

## Services required (minimum)
- fluxer_server (umbrella service)
- Valkey (Redis-compatible KV store)

Optional (enable as needed):
- Meilisearch (search)
- LiveKit (voice/video)

## Database
- SQLite is supported and intended for dev/single-node installs.
- Cassandra is the production backend option.
- For the stated small deployment, SQLite may be sufficient, but confirm with real-world testing.
 - MySQL/Postgres are not supported in the current codebase; consider future work if needed.

## Network and ports (baseline)
- 8080/tcp: fluxer_server HTTP
- 8082/tcp: fluxer_gateway (if exposed separately)
- 6379/tcp: Valkey (internal only)
- 7700/tcp: Meilisearch (internal only)
- 7880/tcp, 7881/tcp, 3478/udp, 50000-50100/udp: LiveKit (voice)

## Reverse proxy
- Apache 2.4 with TLS termination (mod_md/Let’s Encrypt).
- Must pass WebSocket traffic for gateway and any WS endpoints.

## Rocky Linux 9.7 package prereqs (draft)
Two common paths are supported: container-only runtime, or building from source on the host.

Container-only runtime (recommended):
- podman
- podman-compose
- git (for cloning)
- curl (for health checks and downloads)
- httpd (Apache 2.4)
- mod_ssl (TLS)
- mod_md (Let's Encrypt automation, if packaged separately on your system)

Rocky 9.7 dnf example (container-only runtime):
- Enable required repos (if not already enabled):
  - `sudo dnf -y install epel-release`
  - `sudo dnf -y config-manager --set-enabled crb`
- Install packages:
  - `sudo dnf -y install podman podman-compose git curl httpd mod_ssl mod_md`

Build-from-source (host toolchain):
- Node.js 24.x + corepack/pnpm
- build toolchain: gcc, g++, make, python3
- OpenSSL + headers (dev package)
- SQLite library + headers (dev package)
- libvips (image processing)
- libimage-exiftool-perl (image metadata)
- ffmpeg (media processing)
- Erlang/OTP 28 + rebar3 3.24.0 (gateway/relay)
- Rust 1.93.0 toolchain (fluxer_app crates)

Notes:
- Exact package names differ between Debian and RHEL-based systems; map from the Dockerfile apt packages.
- Some packages (e.g., libvips, ffmpeg) may require EPEL on Rocky.

## Rocky 9.7 prereq check (2026-02-20, server run)
Source: `docs/check_prereqs.py --json` run as non-root.

Present:
- podman 5.6.0, podman-compose 1.5.0
- httpd 2.4.62, mod_ssl, mod_md
- git 2.47.3, curl 7.76.1
- gcc/g++ 11.5.0, make 4.3, python3 (system package)
- openssl 3.5.1 + openssl-devel
- sqlite 3.34.1
- ffmpeg 5.1.7

Missing:
- node 24.x (installed: 16.20.2, too old)
- pnpm 10.29.3
- erlang 28.x
- rebar3 3.24.0
- rustc 1.93.0 + cargo
- libvips
- exiftool (perl-Image-ExifTool)
- sqlite-devel

## Rocky 9.7 container-only install run (2026-02-20)
Actions performed:
- Created service user: `useradd -c "Fluxer" -m -u 1110 fluxer`
- Ensured EPEL installed and CRB enabled.
- Installed container runtime + Apache packages.

Upgrades applied during install:
- podman 5.6.0-13.el9_7 (and podman-docker)
- curl/libcurl 7.76.1-35.el9_7.3

## Open questions to resolve in later stages
- Whether fluxer_gateway is exposed via fluxer_server or separately in production.
- Minimum supported OS and versions (Ubuntu/Debian, etc.).
- Precise CPU/RAM requirements from the team or production testing.
- Whether SQLite is acceptable for the stated size long-term.
