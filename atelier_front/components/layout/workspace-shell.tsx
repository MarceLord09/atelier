'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, type ReactNode } from 'react'
import { Masthead } from '@/components/layout/masthead'
import { ModuleNav } from '@/components/layout/module-nav'
import { useAuth } from '@/lib/application/auth/auth-provider'
import { homePath } from '@/lib/domain/role'

export function WorkspaceShell({ children }: { children: ReactNode }) {
  const { ready, user } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (ready && !user) router.replace('/login')
  }, [ready, user, router])

  if (!ready || !user) {
    return (
      <div className="app-shell">
        <header className="masthead">
          <span className="wordmark">ATELIER <span>CONTENT SUITE</span></span>
          <div className="masthead-slot" aria-hidden="true" />
          <div className="masthead-note">Abriendo el taller…</div>
        </header>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <Masthead homeHref={homePath(user.role)} />
      <ModuleNav role={user.role} pathname={pathname} />
      {children}
    </div>
  )
}

export function GuestFrame({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <header className="masthead">
        <Link href="/login" className="wordmark">ATELIER <span>CONTENT SUITE</span></Link>
        <div className="masthead-slot" aria-hidden="true" />
        <div className="masthead-note">CPG / 2026</div>
      </header>
      {children}
    </div>
  )
}
