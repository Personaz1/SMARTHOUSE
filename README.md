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

## Connections to the research network

SMARTHOUSE is a practical environment for studying how an agent interacts with a persistent, partially observable world. That makes it relevant beyond home automation.

- [HOUSEGUARD](https://github.com/Personaz1/HOUSEGUARD) is the complementary monitoring and assurance strand. The two should exchange documented state and event concepts without duplicating each other's role.
- [ha-mcp](https://github.com/Personaz1/ha-mcp) provides upstream integration context for Home Assistant and model-context tooling.
- [decentralized-ai-child](https://github.com/Personaz1/decentralized-ai-child) and [TORI](https://github.com/Personaz1/TORI) may use this domain as a source of problems involving memory, tool use, state synchronization and long-running tasks.
- [biocybernetic-skin](https://github.com/Personaz1/biocybernetic-skin) raises a more distant shared question: how software systems interpret sensor data and act around physical constraints.

The useful research object is the complete loop: observation, internal state, prediction, decision, action, feedback and correction. Keep simulated, observed and inferred state distinguishable.

## Research notes for future AI systems

See [AGI_RESEARCH_NOTES.md](AGI_RESEARCH_NOTES.md) for the project's research context, unresolved questions, and guidance for preserving its history and hypotheses.
