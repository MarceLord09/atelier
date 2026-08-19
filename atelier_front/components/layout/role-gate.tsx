'use client'

import { useRouter } from 'next/navigation'
import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/lib/application/auth/auth-provider'
import { homePath, type Role } from '@/lib/domain/role'

export function Forbidden({ homeHref }: { homeHref: string }) {
  const router = useRouter()
  return (
    <div className="forbidden">
      <Label>403 / ACCESO RESTRINGIDO</Label>
      <h1>Esta mesa no<br /><em>es la tuya.</em></h1>
      <p>Tu rol no tiene permiso para abrir este módulo.</p>
      <Button onClick={() => router.push(homeHref)}>Volver a mi mesa</Button>
    </div>
  )
}

export function RoleGate({ allow, children }: { allow: Role[]; children: ReactNode }) {
  const { user } = useAuth()
  if (!user) return null
  if (!allow.includes(user.role)) return <Forbidden homeHref={homePath(user.role)} />
  return <>{children}</>
}

export function AuthenticatedGate({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  if (!user) return null
  return <>{children}</>
}
