import React, { Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Environment, Grid, Html } from '@react-three/drei'
import { useStore } from '../store'

function Ground() {
  return (
    <group>
      <Grid args={[50, 50]} cellSize={1} cellColor="#444" sectionColor="#666" infiniteGrid />
    </group>
  )
}

function CameraFOV({ position = [0,0,0], rotation=[0,0,0] }: any) {
  return (
    <mesh position={position as any} rotation={rotation as any}>
      <coneGeometry args={[0.6, 2, 16, 1, true]} />
      <meshBasicMaterial color="#00aaff" transparent opacity={0.2} side={2} />
    </mesh>
  )
}

function House() {
  // Simple proxy volumes for rooms
  return (
    <group position={[0, 0, 0]}>
      <mesh position={[0, 0.5, 0]}>
        <boxGeometry args={[10, 1, 8]} />
        <meshStandardMaterial color="#f0f0f0" />
      </mesh>
      <mesh position={[0, 1.1, 0]}>
        <boxGeometry args={[10, 1.2, 8]} />
        <meshStandardMaterial color="#eaeaea" />
      </mesh>
    </group>
  )
}

function Fence() {
  const posts = []
  for (let x = -12; x <= 12; x += 2) posts.push([x, 0.5, -15])
  for (let x = -12; x <= 12; x += 2) posts.push([x, 0.5, 15])
  for (let z = -14; z <= 14; z += 2) posts.push([-12, 0.5, z])
  for (let z = -14; z <= 14; z += 2) posts.push([12, 0.5, z])
  return (
    <group>
      {posts.map((p, i) => (
        <mesh key={i} position={p as any}>
          <boxGeometry args={[0.2, 1, 0.2]} />
          <meshStandardMaterial color="#888" />
        </mesh>
      ))}
    </group>
  )
}

function DevicesOverlay() {
  const devices = useStore((s)=>s.devices)
  return (
    <group>
      {Object.entries(devices).map(([id, d], i) => (
        <Html key={id} position={[ (i%10)-5, 1.5, Math.floor(i/10)-2 ]} distanceFactor={10}>
          <div className="px-1 py-0.5 text-[10px] rounded bg-white/70 border">{id}</div>
        </Html>
      ))}
    </group>
  )
}

export function World3D() {
  return (
    <div className="h-96 border rounded overflow-hidden">
      <Canvas camera={{ position: [8, 8, 8], fov: 60 }}>
        <ambientLight intensity={0.6} />
        <directionalLight position={[5, 10, 5]} intensity={0.7} />
        <Suspense fallback={null}>
          <Environment preset="city" />
        </Suspense>
        <Ground />
        <Fence />
        <House />
        <CameraFOV position={[ -5, 0.1, -4 ]} />
        <CameraFOV position={[ 5, 0.1, 4 ]} rotation={[0, Math.PI, 0]} />
        <DevicesOverlay />
        <OrbitControls />
      </Canvas>
    </div>
  )
}


