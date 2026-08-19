import type { CSSProperties, ReactNode } from 'react'

type BoneRadius = 'sm' | 'md' | 'pill' | 'full'

type BoneProps = {
  width?: string | number
  height?: string | number
  radius?: BoneRadius
  className?: string
}

function toSize(value: string | number) {
  return typeof value === 'number' ? `${value}px` : value
}

export function Bone({ width = '100%', height = 12, radius = 'sm', className = '' }: BoneProps) {
  const style: CSSProperties = { width: toSize(width), height: toSize(height) }
  return <span className={`skeleton skeleton-${radius}${className ? ` ${className}` : ''}`} style={style} aria-hidden="true" />
}

export function BoneStack({ lines = 3, widths }: { lines?: number; widths?: Array<string | number> }) {
  return (
    <div className="skeleton-stack">
      {Array.from({ length: lines }, (_, index) => (
        <Bone key={index} width={widths?.[index] ?? (index === lines - 1 ? '64%' : '100%')} />
      ))}
    </div>
  )
}

function Frame({ label, className, children }: { label: string; className?: string; children: ReactNode }) {
  return (
    <div className={className} role="status" aria-live="polite" aria-busy="true" aria-label={label}>
      <span className="sr-only">{label}</span>
      {children}
    </div>
  )
}

export function BrandBookSkeleton() {
  return (
    <Frame label="Componiendo el manual de marca" className="book-pages">
      {[0, 1, 2].map((page) => (
        <article className="book-page skeleton-page" key={page}>
          <Bone width={28} height={8} />
          <Bone width="42%" height={10} />
          <Bone width="78%" height={34} radius="md" />
          <BoneStack lines={4} widths={['100%', '92%', '80%', '54%']} />
          <Bone width={72} height={72} radius="md" />
        </article>
      ))}
    </Frame>
  )
}

export function RetrievalSkeleton() {
  return (
    <Frame label="Consultando el manual" className="retrieval loading">
      <div className="retrieval-head">
        <Bone width={48} height={10} radius="pill" />
        <Bone width={180} height={12} />
      </div>
      <div className="tickets">
        <Bone width={170} height={32} radius="md" />
        <Bone width={210} height={32} radius="md" />
        <Bone width={190} height={32} radius="md" />
      </div>
    </Frame>
  )
}

export function ProofSheetSkeleton() {
  return (
    <Frame label="Generando pieza creativa" className="proof-sheet">
      <div className="proof-meta">
        <Bone width={110} height={10} />
        <Bone width={90} height={8} />
      </div>
      <div className="skeleton-proof-title">
        <Bone width="70%" height={36} radius="md" />
        <Bone width="42%" height={36} radius="md" />
      </div>
      <BoneStack lines={3} widths={['92%', '88%', '60%']} />
      <div className="proof-bottom">
        <Bone width={160} height={10} />
        <div className="skeleton-actions">
          <Bone width={64} height={32} radius="md" />
          <Bone width={140} height={32} radius="md" />
          <Bone width={110} height={32} radius="md" />
        </div>
      </div>
    </Frame>
  )
}

export function DropzoneSkeleton() {
  return (
    <Frame label="Procesando imagen" className="skeleton-drop">
      <Bone width={260} height={340} radius="md" />
    </Frame>
  )
}

export function AuditPanelSkeleton() {
  return (
    <Frame label="Auditando imagen contra el manual">
      <Bone width="55%" height={28} radius="md" />
      <div className="skeleton-finding">
        <Bone width={22} height={22} radius="full" />
        <BoneStack lines={3} widths={['80%', '100%', '40%']} />
      </div>
      <div className="skeleton-finding">
        <Bone width={22} height={22} radius="full" />
        <BoneStack lines={3} widths={['70%', '96%', '36%']} />
      </div>
      <Bone width="100%" height={40} radius="md" />
    </Frame>
  )
}
