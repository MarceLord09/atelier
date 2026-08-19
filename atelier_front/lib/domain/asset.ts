export type AssetKind = 'PRODUCT_SHEET' | 'VIDEO_SCRIPT'
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
}

export const STATUS_LABEL: Record<AssetStatus, string> = {
  DRAFT: 'BORRADOR',
  PENDING: 'PENDIENTE',
  APPROVED: 'APROBADO',
  REJECTED: 'RECHAZADO',
}
