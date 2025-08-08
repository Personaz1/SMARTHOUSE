"use client"
import React from 'react'
import { getMqtt } from '../lib/mqttClient'
import { cameraSnapshot } from '../lib/coreApi'

export default function SimPanel() {
  const enabled = process.env.NEXT_PUBLIC_UI_ENABLE_SIMULATE === 'true'
  if (!enabled) return null
  async function pub(topic: string, payload: any) {
    const c = getMqtt()
    c.publish(topic, JSON.stringify(payload))
  }
  return (
    <div className="bg-white border rounded p-3 space-y-2">
      <div className="font-semibold">Simulate</div>
      <div className="flex gap-2 flex-wrap">
        <button className="px-3 py-1 border rounded" onClick={() => pub('home/sensor/motion_hall/state', { type: 'motion', value: true, ts: Date.now() })}>Motion hall</button>
        <button className="px-3 py-1 border rounded" onClick={() => pub('vision/events/cam_living', { kind: 'motion', bbox: [1,2,3,4], confidence: 0.9, ts: Date.now() })}>Vision motion</button>
        <button className="px-3 py-1 border rounded" onClick={async () => { const r = await cameraSnapshot('cam_living'); alert(`Snapshot: ${r.bucket}/${r.key}`) }}>Snapshot cam_living</button>
      </div>
    </div>
  )
}


