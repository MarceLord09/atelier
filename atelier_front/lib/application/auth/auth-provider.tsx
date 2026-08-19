'use client'

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { ApiError } from '@/lib/domain/errors'
import type { Role } from '@/lib/domain/role'
import type { User } from '@/lib/domain/user'
import { authApi } from '@/lib/infrastructure/api/auth'
import { sessionStore } from '@/lib/infrastructure/storage/session-store'

type AuthContextValue = {
  ready: boolean
  user: User | null
  login: (email: string, password: string) => Promise<User>
  register: (input: { email: string; password: string; name: string; role: Role }) => Promise<User>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false)
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const stored = sessionStore.read()
    if (!stored) {
      setReady(true)
      return
    }
    authApi
      .me()
      .then((current) => setUser(current))
      .catch((error: unknown) => {
        if (!(error instanceof ApiError && error.status === 401)) console.error(error)
        sessionStore.clear()
        setUser(null)
      })
      .finally(() => setReady(true))
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      ready,
      user,
      async login(email, password) {
        const session = await authApi.login({ email, password })
        setUser(session.user)
        return session.user
      },
      async register(input) {
        const session = await authApi.register(input)
        setUser(session.user)
        return session.user
      },
      async logout() {
        await authApi.logout()
        setUser(null)
      },
    }),
    [ready, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return context
}
