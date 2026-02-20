# Fluxer Self-Hosting Docs Plan

## Context
- Initial prompt (2026-02-20): Create a staged plan to research and document self-hosting for Fluxer, including download/compile/install and validation. Admin has a dedicated server and can test behind Apache 2.4 reverse proxy with TLS termination and mod_md (Let's Encrypt).
- Decision (2026-02-20): Favor rootless Podman + podman-compose under a dedicated `fluxer` user for installation.

## Goals
- Produce complete, accurate self-hosting documentation in `docs/`.
- Keep work in small, verifiable stages with explicit checkpoints.
- Ensure instructions are testable in a real deployment (Apache 2.4 + TLS via mod_md).
- Track future expansion items (e.g., adding MySQL/Postgres backend support).

## Target Detail Level (for the final self-hosting docs)
- Prerequisites and supported environments (OS, CPU/RAM, ports).
- Dependency list with versions or minimums.
- Download and build steps (frontend + backend) with commands.
- Configuration files and required environment variables.
- Database setup and migrations.
- Service management (systemd or equivalent) and logging.
- Reverse proxy setup (Apache 2.4) and TLS termination (mod_md).
- Upgrade steps and backup/restore guidance.
- Troubleshooting and common failure modes.

## Stages

### Stage 1: Project Discovery
Goal: Identify the architecture and components that must be documented.
- Inventory repositories/modules (frontend, backend, services, infra).
- Identify package managers, build tools, and runtime dependencies.
- Locate any existing setup or dev instructions and note gaps.
- Produce a short component map and candidate doc sections.

Deliverables:
- `docs/notes/architecture.md` (component map, ports, data flow).
- `docs/notes/build-tools.md` (toolchain + versions).

### Stage 2: Self-Hosting Requirements Draft
Goal: Draft prerequisites and environment requirements.
- Determine OS support and minimum hardware.
- Identify external services (DB, cache, object storage).
- List required ports and network rules.
 - Note database backend limitations and future expansion ideas (e.g., MySQL/Postgres).

Deliverables:
- `docs/notes/prereqs.md` (OS/ports/deps/services).

### Stage 3: Build & Install Procedure Draft
Goal: Capture exact build and installation steps.
- Frontend build and artifacts location.
- Backend build and runtime entrypoint.
- Config file locations and env vars.
- Database initialization/migrations.
- Example systemd units.

Deliverables:
- `docs/notes/build-install.md` (step-by-step commands).
- `docs/notes/config-reference.md` (env vars + configs).

### Stage 4: Reverse Proxy & TLS
Goal: Provide Apache 2.4 + mod_md guidance.
- VirtualHost layout (HTTP->HTTPS redirect).
- WebSocket/HTTP2 handling if needed.
- Headers, timeouts, and body size limits.
- TLS automation with mod_md and Let's Encrypt.

Deliverables:
- `docs/notes/apache-tls.md` (vhost examples + mod_md notes).

### Stage 5: Validation on Admin Server
Goal: Verify instructions on real infrastructure.
- Admin deploys on dedicated server with domain.
- Capture exact commands used and deviations.
- Record success criteria and any issues.

Deliverables:
- `docs/notes/validation-log.md` (what was tested, results).
- Updates to docs based on findings.

### Stage 6: Final Self-Hosting Docs
Goal: Consolidate into user-facing documentation.
- Assemble `docs/self-hosting.md` from staged notes.
- Add upgrade, backup, troubleshooting sections.
- Add quickstart + production-hardening checklist.

Deliverables:
- `docs/self-hosting.md` (final)
- `docs/self-hosting-checklist.md` (optional concise checklist)

## Validation Checklist (used in Stage 5)
- Clean server with fresh OS install.
- All dependencies installed from documented steps.
- Build completes without manual fixes.
- Service starts and survives reboot.
- Reverse proxy works for HTTP and WebSocket.
- TLS certificates provision automatically via mod_md.
- App is reachable at domain and passes basic smoke test.

## Progress Tracking
- [x] Stage 1 complete
- [x] Stage 2 complete
- [x] Stage 3 complete
- [ ] Stage 4 complete
- [ ] Stage 5 complete
- [ ] Stage 6 complete
