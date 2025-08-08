import React from 'react'

type Msg = { role: 'user' | 'assistant', content: string }

export function ChatPanel() {
  const [msgs, setMsgs] = React.useState<Msg[]>([])
  const [text, setText] = React.useState('')
  async function send() {
    if (!text.trim()) return
    const q = text
    setMsgs((m) => [...m, { role: 'user', content: q }])
    setText('')
    // placeholder: echo back; wire to model router later
    setMsgs((m) => [...m, { role: 'assistant', content: `Эхо: ${q}` }])
  }
  return (
    <div className="border rounded p-3 h-full flex flex-col">
      <h2 className="font-medium">Chat</h2>
      <div className="flex-1 overflow-auto space-y-2 mt-2">
        {msgs.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
            <span className={"inline-block px-2 py-1 rounded " + (m.role==='user'?'bg-blue-100':'bg-neutral-100')}>{m.content}</span>
          </div>
        ))}
      </div>
      <div className="mt-2 flex gap-2">
        <input className="border rounded px-2 py-1 flex-1" value={text} onChange={(e)=>setText(e.target.value)} placeholder="Спроси дом..." />
        <button onClick={send} className="px-3 py-1 bg-black text-white rounded">Send</button>
      </div>
    </div>
  )
}


