# SMARTHOUSE — Local-First Home Automation Architecture

SMARTHOUSE is a local-first smart-home system skeleton. Its current bootstrap centers on MQTT messaging, a core API, configuration validation and observability.

## Current repository scope
- Docker Compose development stack.
- Mosquitto MQTT broker.
- Core API and SmartHomeTools skeleton.
- Device and rule configuration files.
- Prometheus/Grafana monitoring components.

## Design principles
- Local control should remain possible without cloud dependence.
- Device commands should be explicit, authenticated and auditable.
- Tool operations should be idempotent where practical.
- Device state must be distinguished from command acknowledgement.
- Unsafe or ambiguous actions should fail closed.

## Development
The repository includes an example environment file and Docker Compose configuration. Review credentials, network bindings and default dashboard access before running outside an isolated development machine. Never expose unauthenticated control endpoints or monitoring dashboards to the public internet.

## Status
Bootstrap/prototype, not a complete autonomous home platform. The presence of a tool skeleton or dashboard container does not establish reliable device integrations, safety certification or production readiness.

## Roadmap
1. Define device capability and state contracts.
2. Add authentication and authorization for every control surface.
3. Implement command acknowledgement, timeout and rollback semantics.
4. Add simulation and integration tests.
5. Document supported devices and offline behavior.
