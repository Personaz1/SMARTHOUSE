"use client"
import React from 'react'

const panels = [
  { title: 'Tool calls', id: 1 },
  { title: 'Tool latency p90', id: 2 },
  { title: 'Trigger firings', id: 3 },
  { title: 'System health', id: 6 },
]

export default function MetricsPage() {
  const base = process.env.NEXT_PUBLIC_GRAFANA_URL || 'http://localhost:3000'
  // Replace d/uid and panelId to match provisioned dashboard; using simple placeholders
  const dash = `${base}/d/smarthouse/smarthouse-core?orgId=1&kiosk&refresh=5s`
  return (
    <div className="grid grid-cols-2 gap-4">
      {panels.map((p) => (
        <div key={p.id} className="bg-white border rounded overflow-hidden">
          <div className="px-3 py-2 border-b font-semibold">{p.title}</div>
          <iframe className="w-full h-[360px]" src={`${dash}&panelId=${p.id}`} />
        </div>
      ))}
    </div>
  )
}


