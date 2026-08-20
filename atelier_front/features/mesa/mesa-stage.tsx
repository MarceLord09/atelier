'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { ProofSheet } from '@/components/content/proof-sheet'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { ProofSheetSkeleton } from '@/components/ui/skeleton'
import type { Asset, AssetStatus } from '@/lib/domain/asset'
import { KIND_SHORT, STATUS_LABEL } from '@/lib/domain/asset'
import { ApiError } from '@/lib/domain/errors'
import { useBrand } from '@/lib/application/brand/brand-provider'
import { governanceApi } from '@/lib/infrastructure/api/governance'

const FILTERS: AssetStatus[] = ['PENDING', 'APPROVED', 'REJECTED']

function formatWhen(value: string) {
  return new Date(value).toLocaleString('es-PE', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function MesaStage() {
  const { brand } = useBrand()
  const [filter, setFilter] = useState<AssetStatus>('PENDING')
  const [assets, setAssets] = useState<Asset[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [reason, setReason] = useState('')
  const [loading, setLoading] = useState(true)
  const [deciding, setDeciding] = useState(false)
  const [error, setError] = useState('')

  const counts = useMemo(
    () => ({
      PENDING: assets.filter((item) => item.status === 'PENDING').length,
      APPROVED: assets.filter((item) => item.status === 'APPROVED').length,
      REJECTED: assets.filter((item) => item.status === 'REJECTED').length,
    }),
    [assets],
  )
  const queue = useMemo(
    () => assets.filter((item) => item.status === filter),
    [assets, filter],
  )
  const selected = queue.find((item) => item.id === selectedId) ?? queue[0] ?? null

  const load = useCallback(async (keepId?: string | null, silent = false) => {
    if (!silent) setLoading(true)
    setError('')
    try {
      const items = await governanceApi.queue()
      setAssets(items)
      setSelectedId((current) => {
        const preferred = keepId === undefined ? current : keepId
        if (preferred && items.some((item) => item.id === preferred)) return preferred
        return items.find((item) => item.status === 'PENDING')?.id ?? items[0]?.id ?? null
      })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo abrir la cola.')
      setAssets([])
      setSelectedId(null)
    } finally {
      if (!silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load, brand?.id])

  const decide = async (approve: boolean) => {
    if (!selected || selected.status !== 'PENDING') return
    setError('')
    setDeciding(true)
    try {
      await governanceApi.review(selected.id, approve ? 'APPROVE' : 'REJECT')
      setReason('')
      await load(null, true)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo registrar el veredicto.')
    } finally {
      setDeciding(false)
    }
  }

  return (
    <>
      <div className="stage-head">
        <div>
          <Label>MÓDULO 03A — MESA</Label>
          <h1>Desk de aprobación</h1>
          <p>Elige una pieza, contrastala con el manual y deja un veredicto.</p>
        </div>
      </div>
      <div className="desk-grid">
        <aside className="queue">
          <div className="queue-head">
            <Label>COLA</Label>
            <span>{assets.length} piezas</span>
          </div>
          <div className="queue-filters" role="tablist" aria-label="Estado de la cola">
            {FILTERS.map((status) => (
              <button
                type="button"
                role="tab"
                aria-selected={filter === status}
                className={filter === status ? 'selected' : ''}
                onClick={() => {
                  setFilter(status)
                  setError('')
                  const first = assets.find((item) => item.status === status)
                  setSelectedId(first?.id ?? null)
                }}
                key={status}
              >
                <small>{STATUS_LABEL[status]}</small>
                <b>{String(counts[status]).padStart(2, '0')}</b>
              </button>
            ))}
          </div>
          <div className="queue-list">
            {loading && !assets.length && <p className="queue-empty">Abriendo cola…</p>}
            {!loading && !queue.length && <p className="queue-empty">No hay piezas {STATUS_LABEL[filter].toLowerCase()}.</p>}
            {queue.map((item) => (
              <button
                type="button"
                key={item.id}
                className={`queue-item${selected?.id === item.id ? ' selected' : ''}`}
                onClick={() => { setSelectedId(item.id); setError('') }}
              >
                <span className="queue-item-kind">{KIND_SHORT[item.kind]}</span>
                <strong>{item.title}</strong>
                <small>{formatWhen(item.created_at)}</small>
              </button>
            ))}
          </div>
        </aside>
        <section className="desk-review">
          {loading && !selected && <ProofSheetSkeleton />}
          {!loading && !selected && <p className="audit-empty">No hay piezas en este estado.</p>}
          {selected && (
            <>
              <ProofSheet asset={selected} />
              {selected.citations.length > 0 && (
                <div className="desk-rules">
                  <Label>CONTRASTE CON EL MANUAL</Label>
                  <div className="tickets">
                    {selected.citations.map((item, index) => (
                      <span key={item}><i>{String(index + 1).padStart(2, '0')}</i>{item}</span>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
          {error && <p className="form-error">{error}</p>}
          {selected?.status === 'PENDING' && (
            <div className="desk-decision">
              <div>
                <Label>VEREDICTO</Label>
                <p>Esta pieza entra a la marca o vuelve a prensa.</p>
              </div>
              <textarea
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Nota breve para el creador (opcional)…"
              />
              <div className="stamp-bar">
                <Button variant="outline" onClick={() => void decide(false)} disabled={deciding}>Rechazar</Button>
                <Button variant="pine" onClick={() => void decide(true)} disabled={deciding}>Aprobar <span>→</span></Button>
              </div>
            </div>
          )}
        </section>
      </div>
    </>
  )
}
