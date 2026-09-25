import { apiRequest } from '../lib/api'

export type Role = 'EMPLOYEE' | 'MANAGER' | 'FINANCE' | 'PROCUREMENT' | 'ADMIN'
export interface User {
  id: number
  name: string
  email: string
  role: Role
  manager_id: number | null
  manager: { id: number; name: string; email: string } | null
  is_active: boolean
}

interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: User
}

export function login(email: string, password: string) {
  return apiRequest<TokenResponse>('/auth/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
}

export function currentUser(token: string, signal: AbortSignal) {
  return apiRequest<User>('/auth/me', {
    headers: { Authorization: `Bearer ${token}` }, signal,
  })
}
