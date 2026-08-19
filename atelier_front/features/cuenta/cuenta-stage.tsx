'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/lib/application/auth/auth-provider'
import { homePath, ROLE_LABEL } from '@/lib/domain/role'

function initialsOf(name: string) {
  return name.split(' ').map((part) => part[0]).join('')
}

export function CuentaStage() {
  const { user } = useAuth()
  const router = useRouter()
  if (!user) return null
  return (
    <>
      <div className="stage-head">
        <div>
          <Label>CUENTA</Label>
          <h1>Configuración</h1>
          <p>Tu sesión viene del backend. El rol no se cambia desde aquí.</p>
        </div>
        <Button variant="quiet" onClick={() => router.push(homePath(user.role))}>Volver a mi mesa</Button>
      </div>
      <section className="account-panel">
        <div className="account-identity">
          <span className="profile-avatar lg">{initialsOf(user.name)}</span>
          <div>
            <Label>{ROLE_LABEL[user.role]}</Label>
            <h3>{user.name}</h3>
            <p>{user.email}</p>
          </div>
        </div>
        <div className="form-field">
          <label>Nombre para mostrar</label>
          <input value={user.name} readOnly />
        </div>
        <div className="form-field">
          <label>Correo</label>
          <input value={user.email} readOnly />
        </div>
        <div className="form-field">
          <label>Rol</label>
          <input value={ROLE_LABEL[user.role]} readOnly />
        </div>
      </section>
    </>
  )
}
