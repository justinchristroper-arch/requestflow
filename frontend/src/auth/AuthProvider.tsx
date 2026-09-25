import { useCallback, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { ApiError } from '../lib/api'
import { currentUser, login } from './api'
import type { User } from './api'
import { AuthContext } from './context'

// Simple portfolio persistence. XSS can read this token; use hardened HttpOnly
// cookies plus CSRF protection for a sensitive deployment. Never store passwords.
const TOKEN_KEY = 'requestflow.access_token'

function storedToken() {
  try { return localStorage.getItem(TOKEN_KEY) } catch { return null }
}

function expiresAt(token: string): number {
  // Used only to schedule UI logout. The backend verifies signature and identity.
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))) as { exp?: unknown }
    return typeof payload.exp === 'number' && Number.isFinite(payload.exp) ? payload.exp * 1000 : 0
  } catch { return 0 }
}

export default function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(storedToken)
  const activeToken = useRef(token)
  const generation = useRef(0)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(Boolean(token))
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)

  const clearSession = useCallback((message: string | null = null) => {
    activeToken.current = null
    generation.current += 1
    try { localStorage.removeItem(TOKEN_KEY) } catch { /* Storage may be disabled. */ }
    setToken(null)
    setUser(null)
    setLoading(false)
    setError(null)
    setNotice(message)
  }, [])

  const retry = useCallback(() => {
    setLoading(true)
    setError(null)
    setAttempt((value) => value + 1)
  }, [])

  const logout = useCallback(() => clearSession(), [clearSession])
  const sessionMatches = useCallback((expected: string | null) => activeToken.current === expected, [])
  const expireSession = useCallback((expected: string | null) => {
    if (activeToken.current === expected) clearSession('Your session expired or is invalid. Please sign in again.')
  }, [clearSession])

  useEffect(() => {
    if (!token) return
    const remaining = expiresAt(token) - Date.now()
    const controller = new AbortController()
    currentUser(token, controller.signal).then((profile) => {
      if (!controller.signal.aborted && activeToken.current === token) setUser(profile)
    }).catch((reason: unknown) => {
      if (controller.signal.aborted || activeToken.current !== token) return
      if (reason instanceof ApiError && reason.status === 401) {
        clearSession('Your session expired or is invalid. Please sign in again.')
      } else {
        setUser(null)
        setError('Unable to verify your session. Check your connection and try again.')
      }
    }).finally(() => {
      if (!controller.signal.aborted && activeToken.current === token) setLoading(false)
    })
    const timer = window.setTimeout(() => expireSession(token), Math.max(0, Math.min(remaining, 2147483647)))
    return () => { controller.abort(); window.clearTimeout(timer) }
  }, [token, attempt, clearSession, expireSession])

  useEffect(() => {
    function syncStorage(event: StorageEvent) {
      if (event.key === TOKEN_KEY || event.key === null) {
        const next = storedToken()
        activeToken.current = next
        generation.current += 1
        setUser(null)
        setLoading(Boolean(next))
        setToken(next)
        setError(null)
      }
    }
    function verifyOnFocus() {
      // Revalidate in the background so switching tabs does not unmount a draft form.
      if (token) setAttempt((value) => value + 1)
    }
    window.addEventListener('storage', syncStorage)
    window.addEventListener('focus', verifyOnFocus)
    return () => {
      window.removeEventListener('storage', syncStorage)
      window.removeEventListener('focus', verifyOnFocus)
    }
  }, [token])

  async function signIn(email: string, password: string) {
    const attemptGeneration = ++generation.current
    const response = await login(email, password)
    if (generation.current !== attemptGeneration) return
    try { localStorage.setItem(TOKEN_KEY, response.access_token) } catch {
      throw new Error('Browser storage is unavailable. Enable site storage to sign in.')
    }
    setNotice(null)
    setError(null)
    setLoading(true)
    activeToken.current = response.access_token
    setToken(response.access_token)
  }

  return <AuthContext.Provider value={{ token, user, loading, error, notice, signIn, logout, retry, sessionMatches, expireSession }}>
    {children}
  </AuthContext.Provider>
}
