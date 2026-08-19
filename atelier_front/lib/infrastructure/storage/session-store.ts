import type { Session } from '@/lib/domain/user'

const KEY = 'atelier.session'

export const sessionStore = {
  read(): Session | null {
    if (typeof window === 'undefined') return null
    try {
      const raw = window.localStorage.getItem(KEY)
      return raw ? (JSON.parse(raw) as Session) : null
    } catch {
      return null
    }
  },
  write(session: Session) {
    window.localStorage.setItem(KEY, JSON.stringify(session))
  },
  clear() {
    window.localStorage.removeItem(KEY)
  },
}
