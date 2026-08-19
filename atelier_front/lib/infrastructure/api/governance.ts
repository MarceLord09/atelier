import type { Asset, AssetStatus } from '@/lib/domain/asset'
import type { Audit } from '@/lib/domain/audit'
import { api } from '@/lib/infrastructure/http/client'

export const governanceApi = {
  queue(status?: AssetStatus): Promise<Asset[]> {
    const query = status ? `?status=${status}` : ''
    return api<Asset[]>(`/api/v1/governance/queue${query}`)
  },
  review(assetId: string, decision: 'APPROVE' | 'REJECT'): Promise<Asset> {
    return api<Asset>(`/api/v1/governance/assets/${assetId}/review`, {
      method: 'POST',
      body: JSON.stringify({ decision }),
    })
  },
  audit(file: File): Promise<Audit> {
    const body = new FormData()
    body.append('image', file)
    return api<Audit>('/api/v1/governance/audit', { method: 'POST', body })
  },
}
