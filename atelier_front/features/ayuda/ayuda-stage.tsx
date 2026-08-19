'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/lib/application/auth/auth-provider'
import { homePath } from '@/lib/domain/role'

const TOPICS = [
  { id: '01', title: 'DNA', copy: 'El Creador arma el manual de marca. Hasta que no esté indexado en RAG, el resto de mesas no tiene reglas que consultar.' },
  { id: '02', title: 'Prensa', copy: 'Ficha, guion o prompt. Siempre se consulta el manual antes de generar.' },
  { id: '03A', title: 'Mesa', copy: 'El Aprobador A revisa copys. Estados: Pendiente → Aprobado o Rechazado.' },
  { id: '03B', title: 'Visión', copy: 'El Aprobador B sube una imagen. El modelo de visión la contrasta contra el manual.' },
]

export function AyudaStage() {
  const { user } = useAuth()
  const router = useRouter()
  return (
    <>
      <div className="stage-head">
        <div>
          <Label>AYUDA</Label>
          <h1>Guía del taller</h1>
          <p>Cómo se usa cada mesa.</p>
        </div>
        <Button variant="quiet" onClick={() => user && router.push(homePath(user.role))}>Volver a mi mesa</Button>
      </div>
      <div className="account-grid">
        {TOPICS.map((topic) => (
          <article className="help-card" key={topic.id}>
            <Label>{topic.id}</Label>
            <h3>{topic.title}</h3>
            <p>{topic.copy}</p>
          </article>
        ))}
      </div>
    </>
  )
}
