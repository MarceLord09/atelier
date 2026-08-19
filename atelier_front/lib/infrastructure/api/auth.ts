import type { Role } from '@/lib/domain/role'
import type { Session, User } from '@/lib/domain/user'
import { api, persistSession } from '@/lib/infrastructure/http/client'
import { sessionStore } from '@/lib/infrastructure/storage/session-store'

type TokenPayload = {
  access_token: string
  refresh_token: string
  expires_in: number
  user: User
}

export const authApi = {
  async register(input: { email: string; password: string; name: string; role: Role }): Promise<Session> {
    const payload = await api<TokenPayload>('/api/v1/auth/register', {
      method: 'POST',
      auth: false,
      body: JSON.stringify(input),
    })
    return persistSession(payload)
  },

  async login(input: { email: string; password: string }): Promise<Session> {
    const payload = await api<TokenPayload>('/api/v1/auth/login', {
      method: 'POST',
      auth: false,
      body: JSON.stringify(input),
    })
    return persistSession(payload)
  },

  async me(): Promise<User> {
    return api<User>('/api/v1/auth/me')
  },

  async logout(): Promise<void> {
    const refreshToken = sessionStore.read()?.refreshToken
    try {
      if (refreshToken) {
        await api('/api/v1/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshToken }),
        })
      }
    } finally {
      sessionStore.clear()
    }
  },
}
