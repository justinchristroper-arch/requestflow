import type { ReactNode } from 'react'
import { useAuth } from './context'

export default function SessionGate({ children }: { children: ReactNode }) {
  const { loading, error, retry, logout } = useAuth()
  if (loading) return <main className="grid min-h-screen place-items-center"><p role="status">Checking your session…</p></main>
  if (error) return <main className="mx-auto max-w-lg px-6 py-24">
    <h1 className="text-2xl font-semibold">Connection interrupted</h1>
    <p role="alert" className="mt-4 text-slate-600">{error}</p>
    <div className="mt-6 flex gap-4"><button className="rounded-lg bg-teal-700 px-4 py-2 text-white" onClick={retry}>Try again</button><button onClick={logout}>Return to login</button></div>
  </main>
  return children
}
