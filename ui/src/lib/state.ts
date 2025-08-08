import { create } from 'zustand'

type DeviceMap = Record<string, any>
type ZoneMap = Record<string, any>

type EventItem = {
  topic: string
  payload: any
  ts: number
}

type Store = {
  devices: DeviceMap
  zones: ZoneMap
  events: EventItem[]
  health: any
  setSnapshot: (s: Partial<Pick<Store, 'devices' | 'zones' | 'health'>>) => void
  pushEvent: (e: EventItem) => void
  upsertDevice: (id: string, data: any) => void
}

export const useStore = create<Store>((set) => ({
  devices: {},
  zones: {},
  events: [],
  health: {},
  setSnapshot: (s) => set((prev) => ({ ...prev, ...s })),
  pushEvent: (e) => set((prev) => ({ events: [e, ...prev.events].slice(0, 100) })),
  upsertDevice: (id, data) => set((prev) => ({ devices: { ...prev.devices, [id]: data } })),
}))


