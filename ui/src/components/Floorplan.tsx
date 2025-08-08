import React from 'react'
import { useStore } from '../store'

type Anchor = { id: string; x: number; y: number; room?: string }

export function Floorplan() {
  const devices = useStore((s) => s.devices)
  const [anchors, setAnchors] = React.useState<Anchor[]>([])
  const [svg, setSvg] = React.useState<string>('')
  React.useEffect(() => {
    async function load() {
      try {
        const svgRes = await fetch('/cfg/floorplan.svg')
        if (svgRes.ok) setSvg(await svgRes.text())
      } catch {}
      try {
        const aRes = await fetch('/cfg/floorplan.json')
        if (aRes.ok) setAnchors(await aRes.json().then((d)=>d.anchors||[]))
      } catch {}
    }
    load()
  }, [])
  return (
    <div className="relative border rounded p-2">
      <div dangerouslySetInnerHTML={{ __html: svg }} />
      {anchors.map((a) => {
        const st = devices[a.id]
        const on = st?.state === 'ON' || st?.state === true
        return (
          <div key={a.id} className={"absolute -translate-x-1/2 -translate-y-1/2 text-[10px] px-1 py-0.5 rounded " + (on? 'bg-yellow-300':'bg-neutral-300')} style={{ left: a.x, top: a.y }}>
            {a.id}
          </div>
        )
      })}
    </div>
  )
}


