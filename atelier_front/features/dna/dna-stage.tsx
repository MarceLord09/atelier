'use client'

import { useEffect, useState } from 'react'
import { BrandBookSkeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { useBrand } from '@/lib/application/brand/brand-provider'
import type { Brand } from '@/lib/domain/brand'
import { COLOR_NAMES, splitHeading } from '@/lib/domain/brand'
import { ApiError } from '@/lib/domain/errors'
import { brandsApi } from '@/lib/infrastructure/api/brands'

const TONES = ['cercano', 'sobrio', 'profesional', 'irreverente']

const DEFAULT_BRIEF = {
  name: 'Kiwicha Viva',
  product: 'Crocante de kiwicha con cacao',
  audience: 'Personas que buscan una pausa simple',
  tone: 'cercano',
  promise: 'Lo bueno de aquí, para todos los días.',
  forbidden: 'milagroso, superalimento',
}

function BrandBook({ brand, loading, compose }: { brand: Brand | null; loading: boolean; compose: () => void }) {
  const [first, rest] = splitHeading(brand?.name ?? '')
  return (
    <section className={`brand-book ${brand ? 'is-generated' : ''}`}>
      <div className="book-toolbar">
        <Label>MANUAL DE MARCA / V.01</Label>
        <span>{loading ? 'Componiendo…' : brand?.indexed ? `Indexado en RAG · ${new Date(brand.created_at).toLocaleString('es-PE')}` : 'Borrador sin indexar'}</span>
      </div>
      {loading ? <BrandBookSkeleton /> : !brand ? (
        <div className="book-empty">
          <span className="page-number">00</span>
          <h2>El manual<br />se escribe aquí.</h2>
          <p>Compón el DNA para abrir el libro y activar la marca.</p>
          <Button onClick={compose}>Componer manual</Button>
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

export function DnaStage() {
  const { brand, setBrand } = useBrand()
  const [product, setProduct] = useState(brand?.product ?? DEFAULT_BRIEF.product)
  const [audience, setAudience] = useState(brand?.audience ?? DEFAULT_BRIEF.audience)
  const [tone, setTone] = useState(brand?.tone ?? DEFAULT_BRIEF.tone)
  const [promise, setPromise] = useState(brand?.promise ?? DEFAULT_BRIEF.promise)
  const [forbidden, setForbidden] = useState(brand?.forbidden.join(', ') ?? DEFAULT_BRIEF.forbidden)
  const [name, setName] = useState(brand?.name ?? DEFAULT_BRIEF.name)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!brand) return
    setName(brand.name)
    setProduct(brand.product)
    setAudience(brand.audience)
    setTone(brand.tone)
    setPromise(brand.promise)
    setForbidden(brand.forbidden.join(', '))
  }, [brand])

  const compose = async () => {
    setError('')
    setLoading(true)
    try {
      const next = await brandsApi.compose({
        name,
        product,
        audience,
        tone,
        promise,
        forbidden: forbidden.split(',').map((word) => word.trim()).filter(Boolean),
      })
      setBrand(next)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo componer el manual.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="stage-head">
        <div>
          <Label>MÓDULO 01 — DNA</Label>
          <h1>Arquitecta de marca</h1>
          <p>Convierte una intuición en un sistema que todos puedan usar.</p>
        </div>
        <span className="module-status">{loading ? '● COMPONIENDO' : brand?.indexed ? '● MANUAL ACTIVO' : '○ SIN MANUAL'}</span>
      </div>
      <div className="atelier-grid">
        <section className="brief">
          <Label>BRIEF DE MARCA</Label>
          <div className="form-field">
            <label>Nombre de marca</label>
            <input value={name} onChange={(event) => setName(event.target.value)} />
          </div>
          <div className="form-field">
            <label>Producto / concepto</label>
            <input value={product} onChange={(event) => setProduct(event.target.value)} />
          </div>
          <div className="form-field">
            <label>Audiencia</label>
            <input value={audience} onChange={(event) => setAudience(event.target.value)} />
          </div>
          <div className="form-field">
            <label>Tono</label>
            <div className="chips">
              {TONES.map((item) => (
                <button type="button" key={item} className={tone === item ? 'selected' : ''} onClick={() => setTone(item)}>{item}</button>
              ))}
            </div>
          </div>
          <div className="form-field">
            <label>Promesa</label>
            <textarea value={promise} onChange={(event) => setPromise(event.target.value)} />
          </div>
          <div className="form-field">
            <label>Lo que NUNCA debe decirse</label>
            <input value={forbidden} onChange={(event) => setForbidden(event.target.value)} />
          </div>
          {error && <p className="form-error">{error}</p>}
          <Button onClick={() => void compose()} disabled={loading}>Componer manual <span>→</span></Button>
        </section>
        <BrandBook brand={brand} loading={loading} compose={() => void compose()} />
      </div>
    </>
  )
}
