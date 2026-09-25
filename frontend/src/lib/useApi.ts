import { useCallback } from 'react'
import { useAuth } from '../auth/context'
import { ApiError, apiRequest } from './api'

export function useApi() {
  const { token, sessionMatches, expireSession } = useAuth()
  return useCallback(async <T,>(path: string, options: RequestInit = {}): Promise<T> => {
    try {
      const result = await apiRequest<T>(path, { ...options, headers: {
        ...options.headers, Authorization: `Bearer ${token}`, ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      } })
      if (!sessionMatches(token)) throw new DOMException('Session changed', 'AbortError')
      return result
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) expireSession(token)
      throw error
    }
  }, [token, sessionMatches, expireSession])
}

export function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : 'Unable to reach the service. Please try again.'
}
