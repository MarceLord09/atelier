import type { Brand, BrandBrief } from '@/lib/domain/brand'
import { api } from '@/lib/infrastructure/http/client'

export const brandsApi = {
  current(): Promise<Brand> {
    return api<Brand>('/api/v1/brands/current')
  },
  list(): Promise<Brand[]> {
    return api<Brand[]>('/api/v1/brands/catalog')
  },
  activate(brandId: string): Promise<Brand> {
    return api<Brand>(`/api/v1/brands/${brandId}/activate`, { method: 'POST' })
  },
  compose(brief: BrandBrief): Promise<Brand> {
    return api<Brand>('/api/v1/brands/compose', {
      method: 'POST',
      body: JSON.stringify(brief),
    })
  },
}
