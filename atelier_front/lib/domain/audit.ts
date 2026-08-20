export type Finding = {
  n: number
  title: string
  detail: string
  rule: string
  ok: boolean
}

export type Audit = {
  id: string
  brand_id: string
  passed: boolean
  findings: Finding[]
  model: string
  image_name: string
  created_at: string
}
