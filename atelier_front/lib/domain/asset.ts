export type AssetKind = 'PRODUCT_SHEET' | 'VIDEO_SCRIPT' | 'IMAGE_PROMPT'
export type AssetStatus = 'DRAFT' | 'PENDING' | 'APPROVED' | 'REJECTED'

export type Asset = {
  id: string
  brand_id: string
  kind: AssetKind
  title: string
  body: string
  status: AssetStatus
  citations: string[]
  model: string
  created_at: string
}

export const KIND_LABEL: Record<AssetKind, string> = {
  PRODUCT_SHEET: 'Ficha de producto',
  VIDEO_SCRIPT: 'Guion de video',
  IMAGE_PROMPT: 'Prompt de imagen',
}

export const KIND_SHORT: Record<AssetKind, string> = {
  PRODUCT_SHEET: 'Ficha',
  VIDEO_SCRIPT: 'Guion',
  IMAGE_PROMPT: 'Prompt',
}

export const STATUS_LABEL: Record<AssetStatus, string> = {
  DRAFT: 'BORRADOR',
  PENDING: 'PENDIENTE',
  APPROVED: 'APROBADO',
  REJECTED: 'RECHAZADO',
}
