import { useRef, useState } from 'react'
import type { SubmitEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/context'
import { ApiError } from '../lib/api'

const demoPassword = 'RequestFlow-Demo!2026'
const demoAccounts = [
  ['Employee', 'employee@requestflow.demo'],
  ['Manager', 'manager@requestflow.demo'],
  ['Finance', 'finance@requestflow.demo'],
  ['Procurement', 'procurement@requestflow.demo'],
  ['Admin', 'admin@requestflow.demo'],
] as const

export default function Login() {
  const { user, signIn, notice } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const guard = useRef(false)
  if (user) return <Navigate to="/" replace />

  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    if (guard.current) return
    guard.current = true
    setError(null)
    setSubmitting(true)
    try { await signIn(email, password) } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : reason instanceof Error && reason.message.includes('storage') ? reason.message : 'Unable to sign in. Check your connection and try again.')
    } finally { guard.current = false; setSubmitting(false) }
  }

  return <main className="grid min-h-screen place-items-center px-6 py-12">
    <div className="w-full max-w-4xl">
      <div className="mb-8 flex items-center gap-3 text-xl font-bold text-slate-900"><span className="grid size-10 place-items-center rounded-lg bg-teal-700 text-base text-white">RF</span>RequestFlow</div>
      <div className="grid overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm md:grid-cols-[1.05fr_.95fr]">
        <section className="p-7 sm:p-9">
          <p className="text-xs font-bold uppercase tracking-widest text-teal-700">IT & procurement workspace</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">Welcome back</h1>
          <p className="mt-3 text-sm leading-6 text-slate-500">Sign in to follow a request from submission through approval and fulfillment.</p>
          {notice && <p role="status" className="mt-5 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">{notice}</p>}
          <form onSubmit={submit} className="mt-6 space-y-5">
            <div><label htmlFor="email" className="text-sm font-medium text-slate-700">Email address</label><input id="email" name="email" type="email" autoComplete="username" required maxLength={254} value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5" /></div>
            <div><label htmlFor="password" className="text-sm font-medium text-slate-700">Password</label><input id="password" name="password" type="password" autoComplete="current-password" required maxLength={1024} value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5" /></div>
            {error && <p id="login-error" role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{error}</p>}
            <button type="submit" disabled={submitting} className="w-full rounded-lg bg-teal-700 px-4 py-3 text-sm font-semibold text-white hover:bg-teal-800 disabled:opacity-60">{submitting ? 'Signing in…' : 'Sign in'}</button>
          </form>
        </section>
        <aside aria-labelledby="demo-accounts" className="border-t border-slate-200 bg-slate-50 p-7 sm:p-9 md:border-l md:border-t-0">
          <p className="text-xs font-bold uppercase tracking-widest text-teal-700">Portfolio access</p>
          <h2 id="demo-accounts" className="mt-3 text-lg font-semibold text-slate-900">Choose a demo role</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">Select an account to fill the sign-in form. All accounts use <span className="font-medium text-slate-800">{demoPassword}</span>.</p>
          <div className="mt-5 grid gap-2 sm:grid-cols-2 md:grid-cols-1">
            {demoAccounts.map(([role, account]) => <button key={role} type="button" onClick={() => { setEmail(account); setPassword(demoPassword); setError(null) }} className="rounded-lg border border-slate-200 bg-white px-3 py-3 text-left hover:border-teal-300 hover:bg-teal-50">
              <span className="block text-sm font-semibold text-slate-800">{role}</span>
              <span className="mt-0.5 block break-all text-xs text-slate-500">{account}</span>
            </button>)}
          </div>
        </aside>
      </div>
      <p className="mx-auto mt-6 max-w-2xl text-center text-xs leading-5 text-slate-500">Portfolio demonstration using synthetic data. Do not submit real company requests or sensitive information.</p>
    </div>
  </main>
}
