import React from 'react'
import { useStore } from '../store'
import { Floorplan } from './Floorplan'
import { World3D } from './World3D'

export function ConsoleView() {
  const devices = useStore((s) => s.devices)
  const zones = useStore((s) => s.zones)
  const events = useStore((s) => s.events)
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="lg:col-span-2 border rounded p-3 space-y-3">
        <h2 className="font-medium mb-2">World</h2>
        <World3D />
        <h2 className="font-medium mb-2">Floorplan</h2>
        <Floorplan />
      </div>
      <div className="border rounded p-3">
        <h2 className="font-medium">Events</h2>
        <div className="h-64 overflow-auto text-xs mt-2 space-y-1">
          {events.slice().reverse().map((e, i) => (
            <div key={i} className="font-mono">
              <span className="text-neutral-500">{e.type}</span> {JSON.stringify(e)}
            </div>
          ))}
        </div>
      </div>
      <div className="border rounded p-3">
        <h2 className="font-medium">Devices</h2>
        <div className="text-xs grid grid-cols-2 gap-2 mt-2">
          {Object.entries(devices).map(([id, d]) => (
            <div key={id} className="border rounded p-2">
              <div className="font-semibold text-xs">{id}</div>
              <pre className="whitespace-pre-wrap text-[10px]">{JSON.stringify(d)}</pre>
            </div>
          ))}
        </div>
      </div>
      <div className="border rounded p-3">
        <h2 className="font-medium">Zones</h2>
        <pre className="text-xs">{JSON.stringify(zones, null, 2)}</pre>
      </div>
    </div>
  )
}


