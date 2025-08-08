import axios from 'axios'

const BASE = process.env.NEXT_PUBLIC_CORE_BASE_URL || 'http://localhost:8000'

export async function getState() {
  const { data } = await axios.get(`${BASE}/state`)
  return data
}

export async function postAgentCommand(body: { command: string; dry_run?: boolean; confirm?: boolean }) {
  const { data } = await axios.post(`${BASE}/agent/command`, body)
  return data
}

export async function cameraSnapshot(camera_id: string) {
  const { data } = await axios.post(`${BASE}/tools/camera_snapshot`, { camera_id })
  return data as { bucket: string; key: string }
}

export async function controlLight(device_id: string, state: boolean, brightness?: number) {
  const { data } = await axios.post(`${BASE}/tools/control_light`, { device_id, state, brightness })
  return data
}


