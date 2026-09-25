import { lazy, Suspense } from 'react'
import { useAuth } from '../auth/context'
import Overview from './Overview'

const ManagementDashboard = lazy(() => import('./ManagementDashboard'))

export default function Dashboard() {
  const { user } = useAuth()
  return user?.role === 'ADMIN' ? <Suspense fallback={<p role="status">Loading dashboard…</p>}><ManagementDashboard /></Suspense> : <Overview />
}
