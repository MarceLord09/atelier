'use client'

import { useCallback, useEffect, useState } from 'react'
import { ProofSheet } from '@/components/content/proof-sheet'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { ProofSheetSkeleton } from '@/components/ui/skeleton'
import type { Asset, AssetStatus } from '@/lib/domain/asset'
import { STATUS_LABEL } from '@/lib/domain/asset'
import { ApiError } from '@/lib/domain/errors'
import { governanceApi } from '@/lib/infrastructure/api/governance'

const FILTERS: AssetStatus[] = ['PENDING', 'APPROVED', 'REJECTED']

export function MesaStage() {
  const [filter, setFilter] = useState<AssetStatus>('PENDING')
  const [queue, setQueue] = useState<Asset[]>([])
  const [selected, setSelected] = useState<Asset | null>(null)
  const [reason, setReason] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async (status: AssetStatus) => {
    setLoading(true)
    setError('')
    try {
      const items = await governanceApi.queue(status)
      setQueue(items)
      setSelected(items[0] ?? null)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo abrir la cola.')
      setQueue([])
      setSelected(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load(filter)
  }, [filter, load])

  const decide = async (approve: boolean) => {
    if (!selected || selected.status !== 'PENDING') return
    setError('')
    try {
      await governanceApi.review(selected.id, approve ? 'APPROVE' : 'REJECT')
      await load(filter)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo registrar el veredicto.')
    }
  }

  return (
    <>
      <div className="stage-head">
        <div>
          <Label>MÓDULO 03A — MESA</Label>
          <h1>Desk de aprobación</h1>
          <p>Una revisión a la vez. Cada decisión deja una marca.</p>
        </div>
        <span className={`stamp ${STATUS_LABEL[selected?.status ?? filter].toLowerCase()}`}>
          {STATUS_LABEL[selected?.status ?? filter]}
        </span>
      </div>
      <div className="desk-grid">
        <aside className="queue">
          <Label>COLA DE PRODUCCIÓN</Label>
          {FILTERS.map((status) => (
            <button type="button" className={filter === status ? 'selected' : ''} onClick={() => setFilter(status)} key={status}>
              <span className={`stamp-dot ${STATUS_LABEL[status].toLowerCase()}`} />
              {STATUS_LABEL[status]}
              <b>{filter === status ? String(queue.length).padStart(2, '0') : '—'}</b>
            </button>
          ))}
          {queue.map((item) => (
            <button type="button" key={item.id} className={selected?.id === item.id ? 'selected' : ''} onClick={() => setSelected(item)}>
              {item.title}
            </button>
          ))}
        </aside>
        <section>
          {loading && <ProofSheetSkeleton />}
          {!loading && selected && <ProofSheet asset={selected} />}
          {!loading && !selected && <p className="audit-empty">No hay piezas en este estado.</p>}
          {error && <p className="form-error">{error}</p>}
          {selected?.status === 'PENDING' && (
            <>
              <div className="verdict">
                <Label>VEREDICTO</Label>
                <textarea value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Añadir una nota breve (opcional)…" />
              </div>
              <div className="stamp-bar">
                <Button variant="outline" onClick={() => void decide(false)}>RECHAZAR</Button>
                <Button variant="pine" onClick={() => void decide(true)}>APROBAR <span>→</span></Button>
              </div>
            </>
          )}
        </section>
        <aside className="rules-panel">
          <Label>REGLAS RECUPERADAS</Label>
          {(selected?.citations ?? []).map((item) => (
            <p key={item}><span>✓</span>{item}</p>
          ))}
          {!selected?.citations.length && <p>Sin citas todavía.</p>}
        </aside>
      </div>
    </>
  )
}
