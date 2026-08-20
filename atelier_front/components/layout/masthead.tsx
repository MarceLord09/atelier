'use client'

import { ChevronDown, CircleHelp, LogOut, Settings } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useRef, useState } from 'react'
import { useAuth } from '@/lib/application/auth/auth-provider'
import { useBrand } from '@/lib/application/brand/brand-provider'
import type { Brand } from '@/lib/domain/brand'
import { brandInitials } from '@/lib/domain/brand'
import { ROLE_LABEL } from '@/lib/domain/role'
import type { User } from '@/lib/domain/user'

function BrandSwitcher({
  brand,
  brands,
  onSelect,
}: {
  brand: Brand
  brands: Brand[]
  onSelect: (brandId: string) => Promise<void>
}) {
  const [open, setOpen] = useState(false)
  const wrap = useRef<HTMLDivElement>(null)
  const canSwitch = brands.length > 1

  useEffect(() => {
    if (!open) return
    const onPointer = (event: MouseEvent) => {
      if (!wrap.current?.contains(event.target as Node)) setOpen(false)
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <div className="brand-switch" ref={wrap}>
      <button
        type="button"
        className="brand-chip"
        aria-haspopup={canSwitch ? 'listbox' : undefined}
        aria-expanded={canSwitch ? open : undefined}
        onClick={() => canSwitch && setOpen((value) => !value)}
      >
        <span className="brand-mark">{brandInitials(brand.name)}</span>
        <span className="current-brand">{brand.name}</span>
        <span className="chip-swatches" aria-hidden="true">
          {brand.colors.map((color) => <i key={color} style={{ background: color }} />)}
        </span>
        <span className="rag"><span /> RAG</span>
        {canSwitch && <ChevronDown size={14} strokeWidth={1.75} className={open ? 'profile-caret is-open' : 'profile-caret'} />}
      </button>
      {open && (
        <div className="brand-menu" role="listbox">
          {brands.map((item) => (
            <button
              type="button"
              role="option"
              aria-selected={item.id === brand.id}
              className={item.id === brand.id ? 'selected' : ''}
              key={item.id}
              onClick={() => {
                setOpen(false)
                if (item.id !== brand.id) void onSelect(item.id)
              }}
            >
              <span className="brand-mark">{brandInitials(item.name)}</span>
              <span>
                <strong>{item.name}</strong>
                <small>{item.kit_complete ? 'Kit aprobado' : 'DNA activo'}</small>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function initialsOf(name: string) {
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
}

function ProfileMenu({ user, logout }: { user: User; logout: () => Promise<void> }) {
  const [open, setOpen] = useState(false)
  const wrap = useRef<HTMLDivElement>(null)
  const router = useRouter()

  useEffect(() => {
    if (!open) return
    const onPointer = (event: MouseEvent) => {
      if (!wrap.current?.contains(event.target as Node)) setOpen(false)
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const go = (href: string) => {
    setOpen(false)
    router.push(href)
  }

  return (
    <div className="profile-wrap" ref={wrap}>
      <button type="button" className="profile-trigger" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((value) => !value)}>
        <span className="profile-avatar">{initialsOf(user.name)}</span>
        <span className="profile-meta"><strong>{user.name}</strong><small>{ROLE_LABEL[user.role]}</small></span>
        <ChevronDown size={14} strokeWidth={1.75} className={open ? 'profile-caret is-open' : 'profile-caret'} />
      </button>
      {open && (
        <div className="profile-menu" role="menu">
          <button type="button" role="menuitem" onClick={() => go('/configuracion')}><Settings size={15} strokeWidth={1.75} /> Configuración de perfil</button>
          <button type="button" role="menuitem" onClick={() => go('/ayuda')}><CircleHelp size={15} strokeWidth={1.75} /> Ayuda</button>
          <hr />
          <button type="button" role="menuitem" className="danger" onClick={() => { setOpen(false); void logout() }}><LogOut size={15} strokeWidth={1.75} /> Cerrar sesión</button>
        </div>
      )}
    </div>
  )
}

export function Masthead({ homeHref }: { homeHref: string }) {
  const { user, logout } = useAuth()
  const { brand, brands, loading, busy, select } = useBrand()
  const pending = loading || busy
  const indexed = Boolean(brand?.indexed)

  return (
    <header className="masthead">
      <Link href={homeHref} className="wordmark">ATELIER <span>CONTENT SUITE</span></Link>
      {pending ? (
        <div className="brand-chip is-pending">
          <span className="current-brand">{busy ? 'Componiendo el manual…' : 'Abriendo marca…'}</span>
        </div>
      ) : indexed && brand ? (
        <BrandSwitcher brand={brand} brands={brands} onSelect={select} />
      ) : <div className="masthead-slot" aria-hidden="true" />}
      {user ? <ProfileMenu user={user} logout={logout} /> : <div className="masthead-note">CPG / 2026</div>}
    </header>
  )
}
