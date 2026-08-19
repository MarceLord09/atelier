import type { ReactNode } from 'react'

export function Label({ children }: { children: ReactNode }) {
  return <div className="eyebrow">{children}</div>
}
