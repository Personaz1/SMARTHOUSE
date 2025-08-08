# Guardian Unreal Scaffold

This directory will host the Unreal Engine project for GuardianWorld.

Planned components:
- Minimal level with proxy meshes for house, lot, and fence
- Blueprints: LightDevice, CameraDevice (FOV), SirenDevice, DoorLock, DronePawn, DogPawn
- DataAsset mapping `device_id -> Actor`
- Integration options:
  - MQTT client plugin (C++) to subscribe to `home/#`, `vision/events/#`
  - HTTP SSE lightweight client to `/ui/stream`

Workflow:
1. Import GLB assets (same node names as devices) with Datasmith or direct import
2. Assign actors to DataAsset
3. Implement `ApplyState(device_id, payload)` in Blueprints to drive visuals
4. Connect to broker or core SSE in BeginPlay and route messages


