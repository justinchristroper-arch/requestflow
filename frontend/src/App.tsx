import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import AuthProvider from './auth/AuthProvider'
import SessionGate from './auth/SessionGate'
import { useAuth } from './auth/context'
import type { Role } from './auth/api'
import Login from './pages/Login'
import Workspace from './Workspace'
import Dashboard from './pages/Dashboard'
import RequestList from './pages/RequestList'
import CreateRequest from './pages/CreateRequest'
import RequestDetail from './pages/RequestDetail'
import ApprovalQueue from './pages/ApprovalQueue'
import ProcurementQueue from './pages/ProcurementQueue'

function ProtectedWorkspace() {
  const { user } = useAuth()
  return user ? <Workspace /> : <Navigate to="/login" replace />
}

function RoleRoute({ roles }: { roles: Role[] }) {
  const { user } = useAuth()
  return user && roles.includes(user.role) ? <Outlet /> : <Navigate to="/" replace />
}

export default function App() {
  return <BrowserRouter><AuthProvider><SessionGate><Routes>
    <Route path="/login" element={<Login />} />
    <Route element={<ProtectedWorkspace />}>
      <Route path="/" element={<Dashboard />} />
      <Route element={<RoleRoute roles={['EMPLOYEE', 'MANAGER', 'ADMIN']} />}>
        <Route path="/requests" element={<RequestList />} />
      </Route>
      <Route element={<RoleRoute roles={['EMPLOYEE', 'MANAGER']} />}>
        <Route path="/requests/new" element={<CreateRequest />} />
      </Route>
      <Route path="/requests/:id" element={<RequestDetail />} />
      <Route element={<RoleRoute roles={['PROCUREMENT']} />}>
        <Route path="/procurement" element={<ProcurementQueue />} />
      </Route>
      <Route element={<RoleRoute roles={['MANAGER', 'FINANCE']} />}>
        <Route path="/approvals" element={<ApprovalQueue />} />
      </Route>
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></SessionGate></AuthProvider></BrowserRouter>
}
