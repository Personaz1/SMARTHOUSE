import { create } from 'zustand'

type Device = Record<string, any>

type UIEvent = {
  type: string
  ts?: number
  [k: string]: any
}

type State = {
  devices: Record<string, Device>
  zones: Record<string, any>
  security: { mode?: string; ts?: number }
  events: UIEvent[]
  pushEvent: (e: UIEvent) => void
  replaceSnapshot: (snapshot: any) => void
}

export const useStore = create<State>((set) => ({
  devices: {},
  zones: {},
  security: {},
  events: [],
  pushEvent: (e) => set((s) => ({ events: [...s.events.slice(-299), e] })),
  replaceSnapshot: (snapshot) => set(() => ({
    devices: snapshot?.devices || {},
    zones: snapshot?.zones || {},
    security: { mode: snapshot?.security_mode, ts: snapshot?.ts },
  })),
}))


