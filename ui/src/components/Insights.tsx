import React from 'react'
import { useStore } from '../store'

export function Insights() {
  const events = useStore((s) => s.events)
  const insights = events.filter((e) => e.type === 'insight').slice(-50).reverse()
  return (
    <div className="border rounded p-3">
      <h2 className="font-medium">Insights</h2>
      <ul className="text-sm mt-2 list-disc pl-4">
        {insights.map((i, idx) => (
          <li key={idx}>{i.kind} in {i.room}</li>
        ))}
      </ul>
    </div>
  )
}


