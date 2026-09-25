import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from './auth/context'
import { roleLabels } from './requests/display'

export default function Workspace() {
  const { user, logout } = useAuth()
  const path = useLocation().pathname
  const [openPath, setOpenPath] = useState<string | null>(null)
  const menuOpen = openPath === path
  const creator = user?.role === 'EMPLOYEE' || user?.role === 'MANAGER'
  const approver = user?.role === 'MANAGER' || user?.role === 'FINANCE'
  const navigation = [
    { to: '/', label: 'Dashboard' },
    ...(user?.role === 'PROCUREMENT' ? [{ to: '/procurement', label: 'Procurement Queue' }] : []),
    ...(creator || user?.role === 'ADMIN' ? [{ to: '/requests', label: user?.role === 'ADMIN' ? 'Requests' : 'My Requests' }] : []),
    ...(creator ? [{ to: '/requests/new', label: 'Create Request' }] : []),
    ...(approver ? [{ to: '/approvals', label: user?.role === 'FINANCE' ? 'Finance Approvals' : 'Approvals' }] : []),
  ]
  const title = path === '/' ? 'Overview' : path === '/procurement' ? 'Procurement queue' : path === '/requests/new' ? 'Create request' : path === '/approvals' ? 'Approvals' : 'Requests'
  return <div className="min-h-screen lg:grid lg:grid-cols-[240px_minmax(0,1fr)]">
    <a href="#main-content" className="sr-only z-50 rounded bg-teal-800 p-3 text-white focus:not-sr-only focus:fixed focus:left-4 focus:top-4">Skip to content</a>
    <aside className="border-r border-slate-200 bg-white p-5 lg:min-h-screen lg:p-6">
      <div className="flex items-center justify-between gap-4">
      <NavLink className="flex items-center gap-3 text-xl font-bold tracking-tight text-slate-900" to="/"><span className="grid size-9 place-items-center rounded-lg bg-teal-700 text-base text-white">RF</span>RequestFlow</NavLink>
      <button aria-expanded={menuOpen} aria-controls="workspace-navigation" className="secondary-button lg:hidden" onClick={() => setOpenPath(menuOpen ? null : path)}>{menuOpen ? 'Close menu' : 'Menu'}</button></div>
      <p className="mt-2 text-xs text-slate-500">IT & procurement workspace</p>
      <nav id="workspace-navigation" aria-label="Main navigation" className={`${menuOpen ? 'flex' : 'hidden'} mt-5 flex-col gap-2 lg:mt-10 lg:flex`}>{navigation.map((item) => <NavLink key={item.to} to={item.to} end onClick={() => setOpenPath(null)} className={({ isActive }) => `rounded-lg px-4 py-3 text-sm font-semibold ${isActive ? 'bg-teal-50 text-teal-800' : 'text-slate-500 hover:bg-slate-50'}`}>{item.label}</NavLink>)}</nav>
      <p className="mt-10 hidden border-t border-slate-100 pt-5 text-xs leading-6 text-slate-500 lg:block">Request, review, fulfill.<br />One traceable workflow.</p>
    </aside>
    <div className="min-w-0"><header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-6 py-5 lg:px-10"><span className="text-sm text-slate-500">Workspace <span className="mx-2 text-slate-300">/</span> {title}</span><div className="flex flex-wrap items-center gap-4"><span className="text-sm font-medium text-slate-700">{user?.name}</span><span className="rounded-full border border-slate-200 px-3 py-1 text-xs font-medium text-slate-600">{user && roleLabels[user.role]}</span><button onClick={logout} className="text-sm font-medium text-teal-700 hover:underline">Log out</button></div></header>
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-7xl px-5 py-7 sm:px-6 lg:px-10 lg:py-8"><Outlet /></main>
    </div>
  </div>
}

