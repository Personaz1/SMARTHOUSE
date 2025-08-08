import React from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'

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
    es.addEventListener('state_update', (e) => {
      console.log('state_update', e.data)
    })
    es.addEventListener('trigger_fired', (e) => {
      console.log('trigger', e.data)
    })
    es.addEventListener('agent_step', (e) => {
      console.log('agent_step', e.data)
    })
    es.addEventListener('audit_log', (e) => {
      console.log('audit', e.data)
    })
    return () => es.close()
  }, [])
}

function App() {
  const { data } = useHealth()
  useSSE()
  return (
    <div className="p-4 font-sans">
      <h1 className="text-xl font-semibold">Guardian Console</h1>
      <div className="mt-2 text-sm text-neutral-600">Uptime devices/rules: {data?.devices}/{data?.rules}</div>
      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <section className="border rounded p-3">
          <h2 className="font-medium">Floorplan (stub)</h2>
          <div className="text-xs text-neutral-500">Load floorplan.svg and anchors here.</div>
        </section>
        <section className="border rounded p-3">
          <h2 className="font-medium">Events</h2>
          <div className="text-xs text-neutral-500">SSE feed connected. See console logs.</div>
        </section>
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


