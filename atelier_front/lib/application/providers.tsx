'use client'

import type { ReactNode } from 'react'
import { AuthProvider } from '@/lib/application/auth/auth-provider'
import { BrandProvider } from '@/lib/application/brand/brand-provider'

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <BrandProvider>{children}</BrandProvider>
    </AuthProvider>
  )
}
