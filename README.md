# ΔΣ Guardian v2 — Core Bootstrap

Local-first multi-agent home system skeleton. Day-0 deliverables:

- Docker Compose stack: Mosquitto, Core API, Prometheus, Grafana
- Config validation for `configs/devices.json` and `configs/rules.json`
- MQTT client wrapper and SmartHomeTools skeleton (idempotent publish+wait)

## Quick start

1) Copy environment

```bash
cp .env.example .env
```

2) Launch stack

```bash
docker compose up --build
```

3) Check health

```bash
curl http://localhost:8000/health
```

4) Send a demo command (light control)

```bash
curl -X POST http://localhost:8000/agent/command \
  -H 'content-type: application/json' \
  -d '{"command":{"tool":"control_light","args":{"device_id":"light_living_main","state":true,"brightness":50}}}'
```

Grafana: http://localhost:3000 (anonymous)


