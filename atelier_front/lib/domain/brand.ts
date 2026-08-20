export type Brand = {
  id: string
  name: string
  product: string
  audience: string
  tone: string
  promise: string
  manifesto: string
  forbidden: string[]
  colors: string[]
  voice_do: string[]
  voice_dont: string[]
  indexed: boolean
  created_at: string
  kit_complete?: boolean
  current?: boolean
}

export type BrandBrief = {
  product: string
  audience: string
  tone: string
  promise: string
  forbidden: string[]
  name?: string
}

export const COLOR_NAMES = ['OCHRE', 'PAPER', 'CACAO', 'PINE'] as const

export function brandInitials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

export function splitHeading(value: string): [string, string] {
  const parts = value.trim().split(/\s+/)
  if (parts.length < 2) return [value, '']
  return [parts[0], parts.slice(1).join(' ')]
}
