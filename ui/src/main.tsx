import React from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import './index.css'
import { useStore } from './store'
import { ConsoleView } from './components/Console'
import { ChatPanel } from './components/Chat'

const queryClient = new QueryClient()

function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await fetch(import.meta.env.VITE_API_BASE + '/health')
      return res.json()
    },
    refetchInterval: 15000,
  })
}

function useSSE() {
  React.useEffect(() => {
    const url = (import.meta as any).env.VITE_API_BASE + '/ui/stream'
    const es = new EventSource(url)
    es.onmessage = () => {}
    es.addEventListener('heartbeat', () => {})
    const replace = useStore.getState().replaceSnapshot
    const push = useStore.getState().pushEvent
    es.addEventListener('state_update', (e) => {
      try { const data = JSON.parse((e as MessageEvent).data); replace(data.snapshot) } catch {}
    })
    es.addEventListener('trigger_fired', (e) => {
      try { const data = JSON.parse((e as MessageEvent).data); push({ type: 'trigger_fired', ...data }) } catch {}
    })
    es.addEventListener('agent_step', (e) => {
      try { const data = JSON.parse((e as MessageEvent).data); push({ type: 'agent_step', ...data }) } catch {}
    })
    es.addEventListener('audit_log', (e) => {
      try { const data = JSON.parse((e as MessageEvent).data); push({ type: 'audit_log', ...data }) } catch {}
    })
    return () => es.close()
  }, [])
}

function App() {
  const { data } = useHealth()
  useSSE()
  return (
    <div className="p-4 font-sans min-h-screen bg-neutral-50">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Guardian</h1>
        <div className="text-sm text-neutral-600">devices/rules: {data?.devices}/{data?.rules}</div>
      </div>
      <div className="mt-4 grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2"><ConsoleView /></div>
        <div><ChatPanel /></div>
      </div>
    </div>
  )
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
)


