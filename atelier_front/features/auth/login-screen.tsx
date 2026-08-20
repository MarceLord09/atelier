'use client'

import { useRouter } from 'next/navigation'
import { FormEvent, useEffect, useState } from 'react'
import { GuestFrame } from '@/components/layout/workspace-shell'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/lib/application/auth/auth-provider'
import { ApiError } from '@/lib/domain/errors'
import { homePath, ROLE_LABEL, type Role } from '@/lib/domain/role'

const ROLES: Role[] = ['CREATOR', 'APPROVER_A', 'APPROVER_B']

const DEMO: { email: string; password: string; name: string; role: Role }[] = [
  { email: 'lucia@atelier.app', password: 'Atelier2026!', name: 'Lucía Torres', role: 'CREATOR' },
  { email: 'mateo@atelier.app', password: 'Atelier2026!', name: 'Mateo Salazar', role: 'APPROVER_A' },
  { email: 'ines@atelier.app', password: 'Atelier2026!', name: 'Inés Vargas', role: 'APPROVER_B' },
]

export function LoginScreen() {
  const { ready, user, login, register } = useAuth()
  const router = useRouter()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [role, setRole] = useState<Role>('CREATOR')
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)

  useEffect(() => {
    if (ready && user) router.replace(homePath(user.role))
  }, [ready, user, router])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setPending(true)
    try {
      const next = mode === 'login'
        ? await login(email, password)
        : await register({ email, password, name, role })
      router.replace(homePath(next.role))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo entrar.')
    } finally {
      setPending(false)
    }
  }

  return (
    <GuestFrame>
      <main className="login-wrap">
        <div className="login-card">
          <Label>ACCESO AL TALLER</Label>
          <h1>Una mesa para<br /><em>hacerlo bien.</em></h1>
          <p className="lede">Entra con tu correo. El rol abre solo tu mesa.</p>
          <div className="login-rule" />
          {mode === 'login' && (
            <div>
              {DEMO.map((item) => (
                <button
                  key={item.email}
                  type="button"
                  className="demo-user"
                  disabled={pending}
                  onClick={() => {
                    setEmail(item.email)
                    setPassword(item.password)
                    setError('')
                  }}
                >
                  <span className="avatar">{item.name.split(' ').map((part) => part[0]).join('')}</span>
                  <span>
                    <strong>{item.name}</strong>
                    <small>{ROLE_LABEL[item.role]} · {item.email}</small>
                  </span>
                  <span className="arrow">→</span>
                </button>
              ))}
            </div>
          )}
          <form className="login-form" onSubmit={(event) => void submit(event)}>
            {mode === 'register' && (
              <>
                <div className="form-field">
                  <label htmlFor="name">Nombre</label>
                  <input id="name" value={name} onChange={(event) => setName(event.target.value)} required minLength={2} autoComplete="name" />
                </div>
                <div className="form-field">
                  <label htmlFor="role">Rol</label>
                  <select id="role" value={role} onChange={(event) => setRole(event.target.value as Role)}>
                    {ROLES.map((item) => (
                      <option key={item} value={item}>{ROLE_LABEL[item]}</option>
                    ))}
                  </select>
                </div>
              </>
            )}
            <div className="form-field">
              <label htmlFor="email">Correo</label>
              <input id="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" />
            </div>
            <div className="form-field">
              <label htmlFor="password">Contraseña</label>
              <input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} />
            </div>
            {error && <p className="form-error">{error}</p>}
            <Button type="submit" disabled={pending}>{pending ? 'Entrando…' : mode === 'login' ? 'Entrar' : 'Crear cuenta'} <span>→</span></Button>
          </form>
          <button
            type="button"
            className="text-action"
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}
          >
            {mode === 'login' ? 'Crear una cuenta' : 'Ya tengo cuenta'}
          </button>
          <p className="login-foot">Auth real · JWT · FastAPI</p>
        </div>
      </main>
    </GuestFrame>
  )
}
