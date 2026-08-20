'use client'

import { useEffect, useRef, useState, type DragEvent } from 'react'
import { Label } from '@/components/ui/label'
import { useBrand } from '@/lib/application/brand/brand-provider'
import type { Audit } from '@/lib/domain/audit'
import { ApiError } from '@/lib/domain/errors'
import { governanceApi } from '@/lib/infrastructure/api/governance'

const ACCEPT = ['image/jpeg', 'image/png', 'image/webp']
const SCAN_STEPS = [
  'Leyendo el nombre visible',
  'Contrastando la paleta',
  'Revisando voz y claims',
  'Midiendo el área de respeto',
]

function isImageFile(file: File) {
  return ACCEPT.includes(file.type) || /\.(jpe?g|png|webp)$/i.test(file.name)
}

function useScanStep(active: boolean) {
  const [index, setIndex] = useState(0)
  useEffect(() => {
    if (!active) {
      setIndex(0)
      return
    }
    const id = window.setInterval(() => {
      setIndex((current) => (current + 1) % SCAN_STEPS.length)
    }, 1600)
    return () => window.clearInterval(id)
  }, [active])
  return index
}

function ScanOverlay({ step }: { step: number }) {
  return (
    <div className="scan-overlay" role="status" aria-live="polite" aria-label="Analizando imagen contra el manual">
      <span className="scan-corner tl" />
      <span className="scan-corner tr" />
      <span className="scan-corner bl" />
      <span className="scan-corner br" />
      <div className="scan-grid" />
      <div className="scan-beam" />
      <div className="scan-caption">
        <small>Gemini · contrastando DNA</small>
        <b>{SCAN_STEPS[step]}</b>
      </div>
    </div>
  )
}

function ScanPanel({ step }: { step: number }) {
  return (
    <div className="audit-scan" role="status" aria-live="polite">
      <p className="audit-scan-kicker">La IA está leyendo la pieza</p>
      <ol>
        {SCAN_STEPS.map((item, index) => (
          <li key={item} className={index === step ? 'is-active' : index < step ? 'is-done' : ''}>
            <span>{String(index + 1).padStart(2, '0')}</span>
            {item}
          </li>
        ))}
      </ol>
      <div className="audit-scan-bar" aria-hidden="true" />
    </div>
  )
}

export function VisionStage() {
  const { brand } = useBrand()
  const input = useRef<HTMLInputElement>(null)
  const previewUrl = useRef<string | null>(null)
  const dragDepth = useRef(0)
  const [preview, setPreview] = useState<string | null>(null)
  const [audit, setAudit] = useState<Audit | null>(null)
  const [loading, setLoading] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState('')
  const step = useScanStep(loading)

  const pick = () => {
    if (loading) return
    input.current?.click()
  }

  const onFile = async (file: File | undefined) => {
    if (!file || loading) return
    if (!isImageFile(file)) {
      setError('Solo se aceptan JPG, PNG o WEBP.')
      return
    }
    if (previewUrl.current) URL.revokeObjectURL(previewUrl.current)
    const url = URL.createObjectURL(file)
    previewUrl.current = url
    setError('')
    setAudit(null)
    setPreview(url)
    setLoading(true)
    try {
      setAudit(await governanceApi.audit(file))
    } catch (err) {
      setAudit(null)
      if (previewUrl.current) URL.revokeObjectURL(previewUrl.current)
      previewUrl.current = null
      setPreview(null)
      setError(err instanceof ApiError ? err.message : 'No se pudo auditar la imagen.')
    } finally {
      setLoading(false)
    }
  }

  const onDragEnter = (event: DragEvent<HTMLElement>) => {
    event.preventDefault()
    dragDepth.current += 1
    setDragging(true)
  }

  const onDragOver = (event: DragEvent<HTMLElement>) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'copy'
  }

  const onDragLeave = (event: DragEvent<HTMLElement>) => {
    event.preventDefault()
    dragDepth.current -= 1
    if (dragDepth.current <= 0) {
      dragDepth.current = 0
      setDragging(false)
    }
  }

  const onDrop = (event: DragEvent<HTMLElement>) => {
    event.preventDefault()
    event.stopPropagation()
    dragDepth.current = 0
    setDragging(false)
    const file = event.dataTransfer.files[0]
    void onFile(file)
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
        <section
          className={`dropzone${preview ? ' uploaded' : ''}${dragging ? ' is-dragging' : ''}${loading ? ' is-scanning' : ''}`}
          onClick={pick}
          onKeyDown={(event) => { if (event.key === 'Enter') pick() }}
          onDragEnter={onDragEnter}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          role="button"
          tabIndex={0}
          aria-label="Arrastra una imagen o haz clic para seleccionarla"
        >
          <input
            ref={input}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            hidden
            onChange={(event) => {
              void onFile(event.target.files?.[0])
              event.target.value = ''
            }}
          />
          {preview ? (
            <>
              <img
                className={`audit-preview${loading ? ' is-scanning' : ''}`}
                src={preview}
                alt={audit?.image_name ?? 'Pieza en auditoría'}
              />
              {loading && <ScanOverlay step={step} />}
              {audit && !loading && audit.findings.filter((finding) => !finding.ok).map((finding, index) => (
                <button
                  className="marker"
                  style={{
                    left: ['66%', '30%', '72%', '22%'][index] ?? '50%',
                    top: ['30%', '64%', '58%', '28%'][index] ?? '50%',
                  }}
                  key={finding.n}
                  type="button"
                  onClick={(event) => event.stopPropagation()}
                >
                  {finding.n}
                </button>
              ))}
            </>
          ) : (
            <>
              <div className="drop-icon">+</div>
              <h3>{dragging ? 'Suelta para auditar' : 'Arrastra una imagen aquí'}</h3>
              <p>O haz clic · JPG, PNG, WEBP · máximo 8 MB</p>
            </>
          )}
        </section>
        <aside className="audit-panel">
          <Label>CONTRASTE VS. MANUAL</Label>
          {loading ? <ScanPanel step={step} /> : audit ? (
            <>
              <div className={`audit-verdict ${audit.passed ? 'pass' : 'fail'}`}>
                {audit.passed ? 'PASA' : 'NO PASA'}
                <span>
                  {audit.findings.filter((finding) => !finding.ok).length} desvíos · {audit.findings.length} reglas
                </span>
              </div>
              {audit.findings.map((finding) => (
                <div className={`finding${finding.ok ? ' is-ok' : ''}`} key={finding.n}>
                  <b><i>{finding.ok ? '✓' : finding.n}</i>{finding.title}</b>
                  <p>{finding.detail}</p>
                  <small>{finding.rule}</small>
                </div>
              ))}
              <p className="audit-model">Dictamen guardado · {audit.model}</p>
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
