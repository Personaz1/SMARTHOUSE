"use client"
import React from 'react'
import { useStore } from '../lib/state'

export default function Floorplan() {
  const zones = useStore((s) => s.zones)
  const devices = useStore((s) => s.devices)
  return (
    <div className="grid grid-cols-3 gap-4">
      {Object.keys(zones).length === 0 && (
        <div className="col-span-3 text-gray-500">No zones in state yet</div>
      )}
      {Object.entries(zones).map(([name, z]) => (
        <div key={name} className="border rounded p-3 bg-white shadow-sm">
          <div className="font-semibold mb-2">{name}</div>
          <div className="text-sm text-gray-600">presence: {String(z.presence ?? false)}</div>
          <div className="text-sm text-gray-600">illuminance: {z.illuminance ?? '-'} lux</div>
          <div className="mt-2">
            <div className="font-semibold text-sm mb-1">Devices</div>
            <ul className="text-sm list-disc ml-4">
              {Object.entries(devices)
                .filter(([id]) => id.includes(name))
                .map(([id, d]) => (
                  <li key={id} className="truncate">{id}: {d.state ?? d.type ?? ''}</li>
                ))}
            </ul>
          </div>
        </div>
      ))}
    </div>
  )
}


