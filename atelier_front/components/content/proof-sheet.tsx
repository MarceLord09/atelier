'use client'

import type { ReactNode } from 'react'
import { Label } from '@/components/ui/label'
import { KIND_LABEL, STATUS_LABEL, type Asset, type AssetKind } from '@/lib/domain/asset'
import { splitHeading } from '@/lib/domain/brand'

function ProofTitle({ title }: { title: string }) {
  const [first, rest] = splitHeading(title)
  if (!rest) return <>{first}</>
  return <>{first}<br /><em>{rest}</em></>
}

export function ProofSheet({
  asset,
  actions,
}: {
  asset: Asset
  actions?: ReactNode
}) {
  return (
    <article className="proof-sheet">
      <div className="proof-meta">
        <Label>{KIND_LABEL[asset.kind]}</Label>
        <span>{STATUS_LABEL[asset.status]} · {asset.model}</span>
      </div>
      <h2><ProofTitle title={asset.title} /></h2>
      {asset.kind === 'VIDEO_SCRIPT' ? (
        <div className="storyboard">
          {asset.body.split(/(?<=\.)\s+/).filter(Boolean).slice(0, 3).map((line, index) => (
            <div key={line}>
              <b>{String(index + 1).padStart(2, '0')} / TOMA</b>
              <span>{line}</span>
              <small>Manual consultado · {asset.citations.length} fragmentos</small>
            </div>
          ))}
        </div>
      ) : asset.kind === 'IMAGE_PROMPT' ? (
        <p className="proof-copy">{asset.body}</p>
      ) : (
        <p className="proof-copy">{asset.body}</p>
      )}
      <div className="proof-bottom">
        <span>{asset.model} · {asset.citations.length} reglas aplicadas</span>
        <div>{actions}</div>
      </div>
    </article>
  )
}

export function kindFromTab(tab: string): AssetKind {
  if (tab === 'Guion de video') return 'VIDEO_SCRIPT'
  if (tab === 'Prompt de imagen') return 'IMAGE_PROMPT'
  return 'PRODUCT_SHEET'
}
