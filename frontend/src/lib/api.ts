export const apiBaseUrl = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const timeout = AbortSignal.timeout(10000)
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    signal: options.signal ? AbortSignal.any([options.signal, timeout]) : timeout,
  })
  if (!response.ok) {
    let message = 'The service could not complete your request. Please try again.'
    if (response.status === 401) message = 'Your session has expired. Please sign in again.'
    if (response.status < 500) {
      const body: unknown = await response.json().catch(() => null)
      if (body && typeof body === 'object' && 'detail' in body) {
        if (typeof body.detail === 'string') message = body.detail
        else if (Array.isArray(body.detail)) message = body.detail.map((item: { loc?: string[]; msg?: string }) => `${item.loc?.slice(1).join('.') || 'Input'}: ${item.msg || 'Invalid value'}`).join('; ')
      }
    }
    throw new ApiError(response.status, message)
  }
  return response.json() as Promise<T>
}

export async function checkHealth(readiness: boolean, signal: AbortSignal): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/health${readiness ? '/ready' : ''}`, {
    signal: AbortSignal.any([signal, AbortSignal.timeout(8000)]),
  })
  if (!response.ok) throw new Error(`Health check failed: ${response.status}`)
  const body: unknown = await response.json()
  if (typeof body !== 'object' || body === null || !('status' in body) || body.status !== 'ok'
    || (readiness && (!('database' in body) || body.database !== 'connected'))) {
    throw new Error('Unexpected health response')
  }
}
