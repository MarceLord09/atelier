'use client'

import { useEffect, useRef, useState, type CSSProperties, type DragEvent } from 'react'
import { Label } from '@/components/ui/label'
import { useBrand } from '@/lib/application/brand/brand-provider'
import type { Audit, Finding } from '@/lib/domain/audit'
import { ApiError } from '@/lib/domain/errors'
import { governanceApi } from '@/lib/infrastructure/api/governance'

const ACCEPT = ['image/jpeg', 'image/png', 'image/webp']
const SCAN_STEPS = [
  'Leyendo el nombre visible',
  'Contrastando la paleta',
  'Revisando voz y claims',
  'Midiendo el área de respeto',
]

const HEX = /#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b/g

const PIN_FALLBACK: Record<number, { x: number; y: number }> = {
  1: { x: 84, y: 16 },
  2: { x: 48, y: 54 },
  3: { x: 42, y: 70 },
  4: { x: 80, y: 22 },
}

function isImageFile(file: File) {
  return ACCEPT.includes(file.type) || /\.(jpe?g|png|webp)$/i.test(file.name)
}

function isPct(value: number | null | undefined): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 100
}

function pinFor(finding: Finding): { x: number; y: number } {
  if (isPct(finding.x) && isPct(finding.y)) return { x: finding.x, y: finding.y }
  const blob = `${finding.title} ${finding.rule}`.toLowerCase()
  if (blob.includes('nombre')) return PIN_FALLBACK[1]
  if (blob.includes('paleta') || blob.includes('color')) return PIN_FALLBACK[2]
  if (blob.includes('claim') || blob.includes('voz')) return PIN_FALLBACK[3]
  if (blob.includes('respeto') || blob.includes('jerarqu')) return PIN_FALLBACK[4]
  return PIN_FALLBACK[finding.n] ?? { x: 50, y: 50 }
}

function pinStyle(finding: Finding): CSSProperties {
  const pin = pinFor(finding)
  return { left: `${pin.x}%`, top: `${pin.y}%` }
}

function isPaletteFinding(finding: Finding) {
  const blob = `${finding.title} ${finding.rule}`.toLowerCase()
  return blob.includes('paleta') || blob.includes('color')
}

function parseHexes(text: string): string[] {
  const seen = new Set<string>()
  const out: string[] = []
  for (const match of text.matchAll(HEX)) {
    let value = match[0].toUpperCase()
    if (value.length === 4) {
      value = `#${value[1]}${value[1]}${value[2]}${value[2]}${value[3]}${value[3]}`
    }
    if (!seen.has(value)) {
      seen.add(value)
      out.push(value)
    }
  }
  return out
}

function expandHex3(value: string) {
  const hex = value.toUpperCase()
  if (hex.length !== 4) return hex
  return `#${hex[1]}${hex[1]}${hex[2]}${hex[2]}${hex[3]}${hex[3]}`
}

function FindingDetail({ text }: { text: string }) {
  const parts = text.split(/(#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b)/g)
  return (
    <p>
      {parts.map((part, index) =>
        part.startsWith('#') ? (
          <em className="hex-chip" key={`${part}-${index}`}>
            <i style={{ background: expandHex3(part) }} />
            {part.toUpperCase()}
          </em>
        ) : (
          part
        ),
      )}
    </p>
  )
}

function FindingSwatches({ finding, manual }: { finding: Finding; manual: string[] }) {
  if (!isPaletteFinding(finding)) return null
  const cited = parseHexes(finding.detail)
  const dna = manual.map(expandHex3)
  const extras = cited.filter((color) => !dna.includes(color))
  if (dna.length === 0 && extras.length === 0) return null
  return (
    <div className="finding-swatches">
      {dna.length > 0 && (
        <div>
          <span>Manual</span>
          {dna.map((color) => (
            <em key={color} title={color}>
              <i style={{ background: color }} />
              {color}
            </em>
          ))}
        </div>
      )}
      {extras.length > 0 && (
        <div>
          <span>En la pieza</span>
          {extras.map((color) => (
            <em key={color} title={color}>
              <i style={{ background: color }} />
              {color}
            </em>
          ))}
        </div>
      )}
    </div>
  )
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
            <div className="audit-shot">
              <img
                className={`audit-preview${loading ? ' is-scanning' : ''}`}
                src={preview}
                alt={audit?.image_name ?? 'Pieza en auditoría'}
              />
              {loading && <ScanOverlay step={step} />}
              {audit && !loading && audit.findings.filter((finding) => !finding.ok).map((finding) => (
                <button
                  className="marker"
                  style={pinStyle(finding)}
                  key={finding.n}
                  type="button"
                  title={finding.title}
                  onClick={(event) => {
                    event.stopPropagation()
                    document.getElementById(`audit-finding-${finding.n}`)?.scrollIntoView({
                      behavior: 'smooth',
                      block: 'nearest',
                    })
                  }}
                >
                  {finding.n}
                </button>
              ))}
            </div>
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
                <div className={`finding${finding.ok ? ' is-ok' : ''}`} id={`audit-finding-${finding.n}`} key={finding.n}>
                  <b><i>{finding.ok ? '✓' : finding.n}</i>{finding.title}</b>
                  <FindingDetail text={finding.detail} />
                  <FindingSwatches finding={finding} manual={brand?.colors ?? []} />
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
