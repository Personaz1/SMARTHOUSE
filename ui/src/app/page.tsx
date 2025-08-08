"use client"
import React, { useEffect } from 'react'
import Floorplan from '../components/Floorplan'
import EventsFeed from '../components/EventsFeed'
import SimPanel from '../components/SimPanel'
import { getMqtt } from '../lib/mqttClient'
import { getState } from '../lib/coreApi'
import { useStore } from '../lib/state'

export default function Page() {
  const setSnapshot = useStore((s) => s.setSnapshot)
  useEffect(() => {
    getMqtt()
    getState().then((s) => setSnapshot({ devices: s.devices, zones: s.zones, health: s.health }))
  }, [setSnapshot])

  return (
    <div className="grid grid-cols-12 gap-6">
      <div className="col-span-7 space-y-4">
        <Floorplan />
        <SimPanel />
      </div>
      <div className="col-span-5 space-y-4">
        <div className="bg-white border rounded p-3">
          <div className="font-semibold mb-2">Events</div>
          <EventsFeed />
        </div>
      </div>
    </div>
  )
}


