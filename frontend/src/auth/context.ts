import { createContext, useContext } from 'react'
import type { User } from './api'

export interface AuthState {
  token: string | null
  user: User | null
  loading: boolean
  error: string | null
  notice: string | null
  signIn: (email: string, password: string) => Promise<void>
  logout: () => void
  sessionMatches: (expectedToken: string | null) => boolean
  expireSession: (expectedToken: string | null) => void
  retry: () => void
}

export const AuthContext = createContext<AuthState | null>(null)

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('AuthProvider is missing')
  return context
}
