'use client'

import { Plus } from 'lucide-react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useCallback, useEffect, useRef, useState } from 'react'
import { BrandBookSkeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { useBrand } from '@/lib/application/brand/brand-provider'
import type { Brand } from '@/lib/domain/brand'
import { COLOR_NAMES, splitHeading } from '@/lib/domain/brand'
import { ApiError } from '@/lib/domain/errors'
import { brandsApi } from '@/lib/infrastructure/api/brands'

const TONES = ['cercano', 'sobrio', 'profesional', 'irreverente']

const EMPTY_BRIEF = {
  name: '',
  product: '',
  audience: '',
  tone: 'cercano',
  promise: '',
  forbidden: '',
}

const DEFAULT_BRIEF = {
  name: 'Kiwicha Viva',
  product: 'Crocante de kiwicha con cacao',
  audience: 'Personas que buscan una pausa simple',
  tone: 'cercano',
  promise: 'Lo bueno de aquí, para todos los días.',
  forbidden: 'milagroso, superalimento',
}

function BrandBook({
  brand,
  loading,
  compose,
  canCompose,
  loadingCopy = 'Componiendo…',
}: {
  brand: Brand | null
  loading: boolean
  compose: () => void
  canCompose: boolean
  loadingCopy?: string
}) {
  const [first, rest] = splitHeading(brand?.name ?? '')
  const status = loading ? '● CARGANDO' : brand?.indexed ? '● MANUAL ACTIVO' : '○ SIN MANUAL'
  return (
    <section className={`brand-book ${brand && !loading ? 'is-generated' : ''}`}>
      <div className="book-toolbar">
        <Label>MANUAL DE MARCA / V.01</Label>
        <span className="book-toolbar-meta">
          <span className={`module-status${brand?.indexed && !loading ? '' : ' is-idle'}`}>{status}</span>
          <span>
            {loading
              ? loadingCopy
              : brand?.indexed
                ? `Indexado en RAG · ${new Date(brand.created_at).toLocaleString('es-PE')}`
                : 'Borrador sin indexar'}
          </span>
        </span>
      </div>
      {loading ? <BrandBookSkeleton /> : !brand ? (
        <div className="book-empty">
          <span className="page-number">00</span>
          <h2>El manual<br />se escribe aquí.</h2>
          <p>Compón el DNA para abrir el libro y activar la marca.</p>
          <Button onClick={compose} disabled={!canCompose}>Componer manual</Button>
        </div>
      ) : (
        <div className="book-pages">
          <article className="book-page page-essence">
            <span className="page-number">01</span>
            <Label>ESENCIA</Label>
            <h2>{first}{rest ? <><br /><em>{rest}</em></> : null}</h2>
            <p className="manifesto">{brand.manifesto}</p>
            <div className="page-foot">{brand.audience.toUpperCase()}</div>
          </article>
          <article className="book-page">
            <span className="page-number">02</span>
            <Label>VOZ Y REGISTRO</Label>
            <h3>Cálido, directo,<br /><em>cero tecnicismos.</em></h3>
            <div className="do-dont">
              <div>
                <b>HACER</b>
                {brand.voice_do.slice(0, 2).map((line) => <p key={line}>{line}</p>)}
              </div>
              <div>
                <b>EVITAR</b>
                {brand.voice_dont.slice(0, 2).map((line) => <p key={line}>{line}</p>)}
              </div>
            </div>
          </article>
          <article className="book-page">
            <span className="page-number">03</span>
            <Label>SISTEMA VISUAL</Label>
            <div className="swatches">
              {brand.colors.map((color, index) => (
                <div key={color}>
                  <i style={{ background: color }} />
                  <small>{COLOR_NAMES[index] ?? `C${index + 1}`}<br />{color}</small>
                </div>
              ))}
            </div>
            <div className="clearspace">
              <b>ÁREA DE RESPETO</b>
              <span>{first}<br /><em>{rest}</em></span>
            </div>
          </article>
        </div>
      )}
    </section>
  )
}

function fillFromBrand(brand: Brand) {
  return {
    name: brand.name,
    product: brand.product,
    audience: brand.audience,
    tone: brand.tone,
    promise: brand.promise,
    forbidden: brand.forbidden.join(', '),
  }
}

export function DnaStage() {
  const { brand, loading: hydrating, drafting, setBrand, setBusy, beginDraft, cancelDraft, refresh } = useBrand()
  const router = useRouter()
  const params = useSearchParams()
  const nameRef = useRef<HTMLInputElement>(null)
  const seed = brand ? fillFromBrand(brand) : DEFAULT_BRIEF
  const [product, setProduct] = useState(seed.product)
  const [audience, setAudience] = useState(seed.audience)
  const [tone, setTone] = useState(seed.tone)
  const [promise, setPromise] = useState(seed.promise)
  const [forbidden, setForbidden] = useState(seed.forbidden)
  const [name, setName] = useState(seed.name)
  const [composing, setComposing] = useState(false)
  const [error, setError] = useState('')
  const loading = hydrating || composing
  const creatingNew = drafting || (!brand && !hydrating)

  const applyBrief = (brief: typeof EMPTY_BRIEF) => {
    setName(brief.name)
    setProduct(brief.product)
    setAudience(brief.audience)
    setTone(brief.tone)
    setPromise(brief.promise)
    setForbidden(brief.forbidden)
  }

  const startNew = useCallback(() => {
    beginDraft()
    setError('')
    applyBrief(EMPTY_BRIEF)
    window.setTimeout(() => nameRef.current?.focus(), 0)
  }, [beginDraft])

  useEffect(() => {
    if (!brand || drafting) return
    applyBrief(fillFromBrand(brand))
  }, [brand, drafting])

  useEffect(() => {
    if (params.get('nuevo') !== '1') return
    startNew()
    router.replace('/dna')
  }, [params, router, startNew])

  const compose = async () => {
    setError('')
    setComposing(true)
    setBusy(true)
    try {
      const next = await brandsApi.compose({
        name,
        product,
        audience,
        tone,
        promise,
        forbidden: forbidden.split(',').map((word) => word.trim()).filter(Boolean),
      })
      cancelDraft()
      setBrand(next)
      await refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo componer el manual.')
    } finally {
      setComposing(false)
      setBusy(false)
    }
  }

  return (
    <div className="atelier-grid">
      <div>
        <div className="stage-head">
          <div>
            <Label>MÓDULO 01 — DNA</Label>
            <h1>Arquitecta de marca</h1>
            <p>Convierte una intuición en un sistema que todos puedan usar.</p>
          </div>
          <Button variant="outline" onClick={startNew} disabled={loading || drafting} className="new-brand-btn">
            <Plus size={14} strokeWidth={2} /> Nueva marca
          </Button>
        </div>
        <section className="brief">
          <Label>{drafting ? 'BRIEF NUEVO' : 'BRIEF DE MARCA'}</Label>
          {drafting && (
            <p className="login-foot">Campos en blanco. Al componer se crea otra marca y el masthead cambia al DNA nuevo.</p>
          )}
          <div className="form-field">
            <label>Nombre de marca</label>
            <input
              ref={nameRef}
              value={name}
              placeholder="Ej. Blanca Flor"
              disabled={loading}
              onChange={(event) => setName(event.target.value)}
            />
          </div>
          <div className="form-field">
            <label>Producto / concepto</label>
            <input
              value={product}
              placeholder="Ej. panetones premium con pasas y frutas"
              disabled={loading}
              onChange={(event) => setProduct(event.target.value)}
            />
          </div>
          <div className="form-field">
            <label>Audiencia</label>
            <input
              value={audience}
              placeholder="Quién va a usar o comprar esto"
              disabled={loading}
              onChange={(event) => setAudience(event.target.value)}
            />
          </div>
          <div className="form-field">
            <label>Tono</label>
            <div className="chips">
              {TONES.map((item) => (
                <button type="button" key={item} className={tone === item ? 'selected' : ''} disabled={loading} onClick={() => setTone(item)}>{item}</button>
              ))}
            </div>
          </div>
          <div className="form-field">
            <label>Promesa</label>
            <textarea
              value={promise}
              placeholder="La promesa que el copy puede repetir"
              disabled={loading}
              onChange={(event) => setPromise(event.target.value)}
            />
          </div>
          <div className="form-field">
            <label>Lo que NUNCA debe decirse</label>
            <input
              value={forbidden}
              placeholder="harina, horneado"
              disabled={loading}
              onChange={(event) => setForbidden(event.target.value)}
            />
          </div>
          {error && <p className="form-error">{error}</p>}
          {brand?.kit_complete && !drafting && (
            <p className="login-foot">
              Este DNA ya tiene ficha, guion y prompt aprobados. Usa Nueva marca para no sobrescribirlo.
            </p>
          )}
          <div className="brief-actions">
            {drafting && brand ? (
              <Button
                variant="quiet"
                onClick={() => {
                  cancelDraft()
                  applyBrief(fillFromBrand(brand))
                  setError('')
                }}
                disabled={loading}
              >
                Cancelar
              </Button>
            ) : null}
            <Button
              onClick={() => void compose()}
              disabled={loading || !name.trim() || !product.trim() || !audience.trim() || !promise.trim()}
            >
              {creatingNew || (brand && name.trim().toLocaleLowerCase() !== brand.name.toLocaleLowerCase())
                ? 'Componer nueva marca'
                : 'Componer manual'}{' '}
              <span>→</span>
            </Button>
          </div>
        </section>
      </div>
      <BrandBook
        brand={drafting ? null : brand}
        loading={loading}
        loadingCopy={composing ? 'Componiendo…' : 'Cargando marca…'}
        compose={() => void compose()}
        canCompose={!loading && Boolean(name.trim() && product.trim() && audience.trim() && promise.trim())}
      />
    </div>
  )
}
