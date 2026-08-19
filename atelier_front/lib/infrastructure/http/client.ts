import { API_URL } from '@/lib/config'
import { ApiError } from '@/lib/domain/errors'
import type { Session } from '@/lib/domain/user'
import { sessionStore } from '@/lib/infrastructure/storage/session-store'

type TokenPayload = {
  access_token: string
  refresh_token: string
  expires_in: number
  user: Session['user']
}

let refreshInFlight: Promise<boolean> | null = null

function toSession(payload: TokenPayload): Session {
  return {
    accessToken: payload.access_token,
    refreshToken: payload.refresh_token,
    expiresIn: payload.expires_in,
    user: payload.user,
  }
}

async function parseError(response: Response): Promise<ApiError> {
  const data = (await response.json().catch(() => null)) as { error?: { code?: string; message?: string } } | null
  return new ApiError(
    response.status,
    data?.error?.code ?? 'error',
    data?.error?.message ?? 'No se pudo completar la solicitud.',
  )
}

async function refreshTokens(): Promise<boolean> {
  if (refreshInFlight) return refreshInFlight
  refreshInFlight = (async () => {
    const current = sessionStore.read()
    if (!current?.refreshToken) return false
    const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: current.refreshToken }),
    })
    if (!response.ok) {
      sessionStore.clear()
      return false
    }
    const payload = (await response.json()) as TokenPayload
    sessionStore.write(toSession(payload))
    return true
  })()
  try {
    return await refreshInFlight
  } finally {
    refreshInFlight = null
  }
}

type RequestOptions = RequestInit & { auth?: boolean; retry?: boolean }

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { auth = true, retry = true, headers, body, ...rest } = options
  const session = sessionStore.read()
  const isForm = typeof FormData !== 'undefined' && body instanceof FormData
  const response = await fetch(`${API_URL}${path}`, {
    ...rest,
    body,
    headers: {
      ...(isForm || body === undefined ? {} : { 'Content-Type': 'application/json' }),
      ...(auth && session?.accessToken ? { Authorization: `Bearer ${session.accessToken}` } : {}),
      ...headers,
    },
  })

  if (response.status === 401 && auth && retry) {
    const refreshed = await refreshTokens()
    if (refreshed) return api<T>(path, { ...options, retry: false })
    sessionStore.clear()
    throw new ApiError(401, 'unauthorized', 'Sesión expirada.')
  }

  if (response.status === 204) return undefined as T
  if (!response.ok) throw await parseError(response)
  return (await response.json()) as T
}

export function persistSession(payload: TokenPayload): Session {
  const session = toSession(payload)
  sessionStore.write(session)
  return session
}
