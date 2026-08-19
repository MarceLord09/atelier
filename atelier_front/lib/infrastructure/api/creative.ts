import type { Asset, AssetKind } from '@/lib/domain/asset'
import { api } from '@/lib/infrastructure/http/client'

export const creativeApi = {
  generate(input: { kind: AssetKind; prompt: string }): Promise<Asset> {
    return api<Asset>('/api/v1/creative/generate', {
      method: 'POST',
      body: JSON.stringify(input),
    })
  },
  list(): Promise<Asset[]> {
    return api<Asset[]>('/api/v1/creative/assets')
  },
}
