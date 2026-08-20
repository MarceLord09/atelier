'use client'

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useAuth } from '@/lib/application/auth/auth-provider'
import type { Brand } from '@/lib/domain/brand'
import { isNotFound } from '@/lib/domain/errors'
import { brandsApi } from '@/lib/infrastructure/api/brands'

type BrandContextValue = {
  brand: Brand | null
  brands: Brand[]
  loading: boolean
  busy: boolean
  setBrand: (brand: Brand | null) => void
  setBusy: (busy: boolean) => void
  refresh: () => Promise<void>
  select: (brandId: string) => Promise<void>
}

const BrandContext = createContext<BrandContextValue | null>(null)

export function BrandProvider({ children }: { children: ReactNode }) {
  const { user, ready } = useAuth()
  const [brand, setBrand] = useState<Brand | null>(null)
  const [brands, setBrands] = useState<Brand[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  const refresh = useCallback(async () => {
    if (!user) {
      setBrand(null)
      setBrands([])
      setLoading(false)
      return
    }
    setLoading(true)
    try {
      const items = await brandsApi.list()
      setBrands(items)
      setBrand(items.find((item) => item.current) ?? items[0] ?? null)
    } catch (error) {
      if (isNotFound(error)) {
        setBrand(null)
        setBrands([])
      } else console.error(error)
    } finally {
      setLoading(false)
    }
  }, [user])

  const select = useCallback(async (brandId: string) => {
    const next = await brandsApi.activate(brandId)
    setBrand(next)
    setBrands((current) =>
      current.map((item) => ({ ...item, current: item.id === next.id })),
    )
  }, [])

  useEffect(() => {
    if (!ready) return
    void refresh()
  }, [ready, refresh])

  const value = useMemo(
    () => ({ brand, brands, loading, busy, setBrand, setBusy, refresh, select }),
    [brand, brands, loading, busy, refresh, select],
  )

  return <BrandContext.Provider value={value}>{children}</BrandContext.Provider>
}

export function useBrand(): BrandContextValue {
  const context = useContext(BrandContext)
  if (!context) throw new Error('useBrand debe usarse dentro de BrandProvider')
  return context
}
