'use client'

import { useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { AuditPanelSkeleton, DropzoneSkeleton } from '@/components/ui/skeleton'
import { useBrand } from '@/lib/application/brand/brand-provider'
import type { Audit } from '@/lib/domain/audit'
import { ApiError } from '@/lib/domain/errors'
import { governanceApi } from '@/lib/infrastructure/api/governance'

export function VisionStage() {
  const { brand } = useBrand()
  const input = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [audit, setAudit] = useState<Audit | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const pick = () => {
    if (loading) return
    input.current?.click()
  }

  const onFile = async (file: File | undefined) => {
    if (!file) return
    setError('')
    setLoading(true)
    setPreview(URL.createObjectURL(file))
    try {
      setAudit(await governanceApi.audit(file))
    } catch (err) {
      setAudit(null)
      setPreview(null)
      setError(err instanceof ApiError ? err.message : 'No se pudo auditar la imagen.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="stage-head">
        <div>
          <Label>MÓDULO 03B — VISIÓN</Label>
          <h1>Lightbox de auditoría</h1>
          <p>Contraste visual contra el manual activo.</p>
        </div>
      </div>
      <div className="lightbox-grid">
        <section className={`dropzone ${preview ? 'uploaded' : ''}`} onClick={pick} onKeyDown={(event) => { if (event.key === 'Enter') pick() }} role="button" tabIndex={0}>
          <input
            ref={input}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            hidden
            onChange={(event) => void onFile(event.target.files?.[0])}
          />
          {preview && audit ? (
            <>
              <img className="audit-preview" src={preview} alt={audit.image_name} />
              {audit.findings.map((finding) => (
                <button className="marker" style={{ left: finding.n === 1 ? '66%' : '30%', top: finding.n === 1 ? '30%' : '64%' }} key={finding.n} type="button" onClick={(event) => event.stopPropagation()}>{finding.n}</button>
              ))}
            </>
          ) : loading ? (
            <DropzoneSkeleton />
          ) : (
            <>
              <div className="drop-icon">+</div>
              <h3>Coloca una imagen aquí</h3>
              <p>JPG, PNG · máximo 10 MB</p>
            </>
          )}
        </section>
        <aside className="audit-panel">
          <Label>CONTRASTE VS. MANUAL</Label>
          {loading ? <AuditPanelSkeleton /> : audit ? (
            <>
              <div className={`audit-verdict ${audit.passed ? 'pass' : 'fail'}`}>
                {audit.passed ? 'PASA' : 'NO PASA'} <span>{audit.findings.length} hallazgos</span>
              </div>
              {audit.findings.map((finding) => (
                <div className="finding" key={finding.n}>
                  <b><i>{finding.n}</i>{finding.title}</b>
                  <p>{finding.detail}</p>
                  <small>{finding.rule}</small>
                </div>
              ))}
              <Button variant={audit.passed ? 'pine' : 'primary'}>Dictamen {audit.model}</Button>
            </>
          ) : (
            <div className="audit-empty">
              {error || (brand?.indexed ? 'La auditoría aparecerá cuando coloques una imagen.' : 'Compón el DNA antes de auditar.')}
            </div>
          )}
        </aside>
      </div>
    </>
  )
}
