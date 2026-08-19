import type { Role } from '@/lib/domain/role'

export type User = {
  id: string
  email: string
  name: string
  role: Role
  home_route: string
}

export type Session = {
  accessToken: string
  refreshToken: string
  expiresIn: number
  user: User
}
