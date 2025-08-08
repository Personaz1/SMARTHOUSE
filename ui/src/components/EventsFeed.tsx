"use client"
import React from 'react'
import { useStore } from '../lib/state'

export default function EventsFeed() {
  const events = useStore((s) => s.events)
  return (
    <div className="space-y-2">
      {events.slice(0, 20).map((e, i) => (
        <div key={i} className="bg-white border rounded p-2 text-sm">
          <div className="text-gray-600">{new Date(e.ts).toLocaleTimeString()} — <span className="font-mono">{e.topic}</span></div>
          <pre className="text-xs whitespace-pre-wrap break-words">{JSON.stringify(e.payload)}</pre>
        </div>
      ))}
      {events.length === 0 && <div className="text-gray-500">No events yet</div>}
    </div>
  )
}


