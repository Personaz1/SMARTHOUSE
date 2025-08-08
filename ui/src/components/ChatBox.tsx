"use client"
import React, { useState } from 'react'
import { postAgentCommand } from '../lib/coreApi'

type Hist = { cmd: string; result: any }[]

export default function ChatBox() {
  const [input, setInput] = useState('')
  const [hist, setHist] = useState<Hist>([])

  async function send() {
    const cmd = input.trim()
    if (!cmd) return
    setInput('')
    const result = await postAgentCommand({ command: cmd, dry_run: false })
    setHist((h) => [{ cmd, result }, ...h])
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input className="border rounded px-3 py-2 flex-1" placeholder="Введите команду…" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key==='Enter' && send()} />
        <button className="px-4 py-2 rounded bg-blue-600 text-white" onClick={send}>Send</button>
      </div>
      <div className="space-y-3">
        {hist.map((h, i) => (
          <div key={i} className="bg-white border rounded p-3">
            <div className="font-semibold">{h.cmd}</div>
            <pre className="text-xs whitespace-pre-wrap break-words">{JSON.stringify(h.result, null, 2)}</pre>
          </div>
        ))}
        {hist.length === 0 && <div className="text-gray-500">Нет сообщений</div>}
      </div>
      <div className="flex gap-2">
        <button className="px-3 py-1 border rounded" onClick={() => setInput('подготовь дом к ночи')}>Шаблон: Ночной режим</button>
        <button className="px-3 py-1 border rounded" onClick={() => setInput('поставь на охрану')}>Шаблон: Охрана</button>
        <button className="px-3 py-1 border rounded" onClick={() => setInput('включи свет в гостиной 30%')}>Шаблон: Свет 30%</button>
      </div>
    </div>
  )
}


