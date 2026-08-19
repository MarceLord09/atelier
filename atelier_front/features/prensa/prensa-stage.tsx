'use client'

import { useState } from 'react'
import { kindFromTab, ProofSheet } from '@/components/content/proof-sheet'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { ProofSheetSkeleton, RetrievalSkeleton } from '@/components/ui/skeleton'
import { useBrand } from '@/lib/application/brand/brand-provider'
import type { Asset } from '@/lib/domain/asset'
import { ApiError } from '@/lib/domain/errors'
import { creativeApi } from '@/lib/infrastructure/api/creative'

const TABS = ['Ficha de producto', 'Guion de video', 'Prompt de imagen'] as const

function RetrievalStrip({ status, citations }: { status: 'idle' | 'loading' | 'ready'; citations: string[] }) {
  if (status === 'idle') {
    return (
      <div className="retrieval idle">
        <div className="retrieval-head">
          <span className="rag idle"><span /> RAG</span>
          <b>En espera · consulta el manual antes de generar</b>
        </div>
      </div>
    )
  }
  if (status === 'loading') return <RetrievalSkeleton />
  return (
    <div className="retrieval">
      <div className="retrieval-head">
        <span className="rag"><span /> RAG</span>
        <b>Manual consultado</b>
      </div>
      <div className="tickets">
        {citations.slice(0, 4).map((item, index) => (
          <span key={item}><i>{String(index + 1).padStart(2, '0')}</i>{item}</span>
        ))}
      </div>
    </div>
  )
}

export function PrensaStage() {
  const { brand } = useBrand()
  const [tab, setTab] = useState<(typeof TABS)[number]>('Ficha de producto')
  const [prompt, setPrompt] = useState('Presentar Kiwicha Viva como una pausa cotidiana, sabrosa y de origen local.')
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready'>('idle')
  const [asset, setAsset] = useState<Asset | null>(null)
  const [error, setError] = useState('')

  const consult = async () => {
    setError('')
    setStatus('loading')
    try {
      const next = await creativeApi.generate({ kind: kindFromTab(tab), prompt })
      setAsset(next)
      setStatus('ready')
    } catch (err) {
      setStatus('idle')
      setError(err instanceof ApiError ? err.message : 'No se pudo generar.')
    }
  }

  return (
    <>
      <div className="stage-head">
        <div>
          <Label>MÓDULO 02 — PRENSA</Label>
          <h1>Motor creativo</h1>
          <p>Primero el manual. Después, la idea.</p>
        </div>
      </div>
      <div className="press-tabs">
        {TABS.map((item) => (
          <button type="button" className={tab === item ? 'active' : ''} onClick={() => { setTab(item); setStatus('idle'); setAsset(null) }} key={item}>{item}</button>
        ))}
      </div>
      <div className="press-layout">
        <section className="press-input">
          <Label>BRIEF DE SALIDA</Label>
          <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} />
          {error && <p className="form-error">{error}</p>}
          <Button onClick={() => void consult()} disabled={status === 'loading' || !brand?.indexed}>
            Consultar manual <span>→</span>
          </Button>
          {!brand?.indexed && <p className="login-foot">Compón el DNA antes de generar.</p>}
        </section>
        <section>
          <RetrievalStrip status={status} citations={asset?.citations ?? []} />
          {status === 'loading' && <ProofSheetSkeleton />}
          {status === 'ready' && asset && (
            <ProofSheet
              asset={asset}
              actions={
                <>
                  <Button variant="quiet" onClick={() => void navigator.clipboard.writeText(asset.body)}>Copiar</Button>
                  <Button variant="quiet" onClick={() => void consult()}>Regenerar</Button>
                  <Button variant="primary" disabled>En cola de mesa</Button>
                </>
              }
            />
          )}
        </section>
      </div>
    </>
  )
}
