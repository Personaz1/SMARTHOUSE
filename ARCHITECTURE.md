## ΔΣ Guardian v2 — Architecture Overview (GO)

### System Goals
- Local-first, agent-of-agents home system with digital twin stubs
- Unified bus: MQTT primary, REST control, basic vision events
- Idempotent control with state confirmation, safety, audit, and metrics

### Runtime Topology (Docker)
- mosquitto: MQTT broker (1883)
- core: FastAPI app (8000) — API, tools, triggers, supervisor, metrics
- prometheus: scraping `core:8000/metrics`
- grafana: provisioned dashboards (anonymous by default)
- minio: S3-compatible storage (9000/9001) for camera snapshots
- sim (dev-only): echo simulator (MQTT responder + HTTP JPEG)

Prod override: `docker-compose.prod.yml` (restart policies, resource limits, sim disabled by profile, hardened env toggles).

### Core Service (`core/app`)
- Entry: `main.py`
  - Startup: load configs (`ConfigLoader`), init MQTT (`AsyncMqttClient`), `SmartHomeTools`, `HomeContextManager`, `TriggerEngine`, `Supervisor`
  - Endpoints:
    - Health: `GET /health`
    - State: `GET /state` (snapshot: security/occupancy/zones/devices/health)
    - Devices: `GET /devices`, `GET /device/{id}`
    - Configs: `GET /config/devices`, `GET /config/rules`
    - Rules: `POST /rules` (hot-reload, version bump), `DELETE /rules/{id}`
    - Tools: `POST /tools/*` (control_light, set_thermostat, lock/unlock, cover_set_position, switch_on/off, siren_on/off, arm/disarm, camera_snapshot)
    - Agent: `POST /agent/command` (structured tool or intent via Supervisor)
    - Router: `GET /router/backends`, `POST /router/reload`
  - Metrics middleware exposed at `/metrics` via Instrumentator

#### Configuration (`config.py`)
- JSON loading + validation (Draft 2020-12) for `devices.json` and `rules.json` against schemas

#### MQTT Integration (`integration/mqtt_client.py`)
- `publish_json`, `publish_and_wait`, `wait_for_state`, `publish_without_wait` using `aiomqtt`
- Metrics: `mqtt_publish_total`, `mqtt_wait_time_ms`

#### Smart Home Tools (`tools/smarthome.py`)
- Idempotent publish+wait per device type; payload contracts:
  - light: `{type:"light", state:"ON|OFF", brightness? 0..100}`
  - lock: `{type:"lock", state:"LOCKED|UNLOCKED"}`
  - cover: `{type:"cover", position:0..100}`
  - switch: `{type:"switch", state:"ON|OFF"}`
  - thermostat: `{type:"thermostat", target:number}`
  - siren: `{type:"siren", state:"ON|OFF"}`
  - security: `{type:"security", mode:"away|night|home|disarmed"}`
- Camera snapshot: fetch JPEG from sim HTTP, store to MinIO bucket `snapshots` at `{camera_id}/{ts}.jpg`

#### State Context (`state/context.py`)
- Dedicated MQTT client; subscribes `home/#` and `vision/events/#`
- Maintains global snapshot: devices map, zones aggregation by room, health, ts

#### Trigger Engine (`triggers/engine.py`)
- Supports rule types: `time`, `sensor`
- Conditions: `sensor_id` with `equals` subset match, or `topic` (e.g., `vision/events/cam_living`)
- Guards: `debounce_ms`, `throttle_per_min`, `retry{max,backoff_ms}`
- Safety: `rate_limit_per_min` on rule
- Actions: currently `control_light` and `notify` stub
- Metric: `trigger_firings_total{rule_id,result}`

#### Supervisor Agent (`agent/supervisor.py`)
- Minimal ReAct plan for "prepare house for night": dim light + arm security(night)
- Critical tools: `lock_door`, `arm_security` with per-minute rate limit window
- Metrics: `agent_step_latency_ms`, `critical_actions_total`; aggregate `agent_commands_total` in API

#### RBAC & Audit
- `RBAC` stub (allow-all by default in current tree)
- `AuditLogger` writes JSONL entries: actor, role, action, args_hash, result, latency_ms, trace_id

### API Models (`models.py`)
- Pydantic request models for tool endpoints (validation ranges for brightness/position/temp)

### Model Router (`api_router.py`)
- YAML-driven config at `/configs/router.yaml`
- Endpoints: `/router/backends`, `/router/reload`

### Simulator (`sim/echo_sim`)
- MQTT echo of device `set` to `state`, with jitter, 2% drops, quantization (brightness to nearest 5)
- Emits `vision/events/cam_living` motion periodically
- HTTP: `/sim/health`, `/sim/time`, `/sim/camera/{id}/frame` (static JPEG)

### Observability (`monitoring`, `infra/grafana`)
- Prometheus scrape core
- Grafana provisioned dashboard panels: tool calls, latency p90, triggers, agent commands, MQTT wait p90, system health
- Metrics surface: `tool_calls_total`, `tool_call_latency_ms`, `mqtt_publish_total`, `mqtt_wait_time_ms`, `trigger_firings_total`, `agent_commands_total`, `agent_step_latency_ms`, `critical_actions_total`, `rules_version`

### Storage (MinIO)
- S3 endpoint configurable via env; snapshots bucket `snapshots`
- Credentials via env or `.env` file

### Configuration & Schemas (`configs`)
- `devices.json` — registry (id, type, room, topics)
- `rules.json` — example rules; hot-reload via API; presets under `configs/presets/`
- Schemas: `devices.schema.json`, `rules.schema.json`

### MQTT Topics (contracts)
- Device control: `home/device/<id>/set` → state on `home/device/<id>/state`
- Security: `home/security/set` → `home/security/state`
- Vision events: `vision/events/<camera_id>` with `{kind:motion, ...}`

### Deployment
- Dev: `docker compose up --build`
- Prod: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- systemd unit sample for edge-boot
- Backup: configs + MinIO mirror snapshot

### Security Posture (current)
- Anonymous Grafana enabled by default (can disable)
- Secrets via `.env` supported (MinIO creds), recommend overriding defaults
- RBAC placeholder — critical tool gating handled in Supervisor; fuller policy TBD

### Invariants & Design Choices
- Idempotent tool calls: publish+wait with match predicates and bounded timeouts
- Local-first: no external model calls in core path; Router is config-only stub
- Fault-tolerance via jitter/drop in sim to test guards, retries, and idempotency

### Known Gaps / Next Steps
- Expand Trigger actions (siren, lock/unlock, notify sinks)
- Security Agent policy graph (armed modes, escalation, Telegram webhook)
- Model Router backends (Ollama/vLLM/Triton) and selection policies
- ROS2/MoveIt2 bridge stubs for actuators
- RBAC policies and secrets hardening (disable Grafana anonymous in prod)
- Install script for edge nodes; richer health and readiness probes


