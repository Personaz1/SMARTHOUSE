import './globals.css'
import React from 'react'

export const metadata = { title: 'Guardian v2 UI' }

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">
        <nav className="flex items-center gap-6 px-6 py-3 border-b bg-white">
          <a href="/" className="font-semibold">Dashboard</a>
          <a href="/chat" className="font-semibold">Chat</a>
          <a href="/metrics" className="font-semibold">Metrics</a>
        </nav>
        <main className="p-6">{children}</main>
      </body>
    </html>
  )
}


