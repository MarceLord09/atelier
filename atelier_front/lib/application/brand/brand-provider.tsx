'use client'

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useAuth } from '@/lib/application/auth/auth-provider'
import type { Brand } from '@/lib/domain/brand'
import { isNotFound } from '@/lib/domain/errors'
import { brandsApi } from '@/lib/infrastructure/api/brands'

type BrandContextValue = {
  brand: Brand | null
  loading: boolean
  setBrand: (brand: Brand | null) => void
  refresh: () => Promise<void>
}

const BrandContext = createContext<BrandContextValue | null>(null)

export function BrandProvider({ children }: { children: ReactNode }) {
  const { user, ready } = useAuth()
  const [brand, setBrand] = useState<Brand | null>(null)
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    if (!user) {
      setBrand(null)
      return
    }
    setLoading(true)
    try {
      setBrand(await brandsApi.current())
    } catch (error) {
      if (isNotFound(error)) setBrand(null)
      else console.error(error)
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    if (!ready) return
    void refresh()
  }, [ready, refresh])

  const value = useMemo(
    () => ({ brand, loading, setBrand, refresh }),
    [brand, loading, refresh],
  )

  return <BrandContext.Provider value={value}>{children}</BrandContext.Provider>
}

export function useBrand(): BrandContextValue {
  const context = useContext(BrandContext)
  if (!context) throw new Error('useBrand debe usarse dentro de BrandProvider')
  return context
}
