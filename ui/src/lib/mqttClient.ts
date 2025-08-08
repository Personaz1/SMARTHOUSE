import mqtt, { MqttClient } from 'mqtt'
import { useStore } from './state'

let client: MqttClient | null = null

export function getMqtt() {
  if (!client) {
    const url = process.env.NEXT_PUBLIC_MQTT_WS_URL!
    client = mqtt.connect(url)
    client.on('connect', () => {
      client?.subscribe('home/sensor/#')
      client?.subscribe('home/device/#')
      client?.subscribe('vision/events/#')
    })
    client.on('message', (topic, payload) => {
      try {
        const data = JSON.parse(payload.toString())
        const ts = Date.now()
        useStore.getState().pushEvent({ topic, payload: data, ts })
        if (topic.startsWith('home/device/')) {
          const id = topic.split('/')[2]
          useStore.getState().upsertDevice(id, data)
        }
      } catch (_) {
        // ignore parse errors
      }
    })
  }
  return client
}


