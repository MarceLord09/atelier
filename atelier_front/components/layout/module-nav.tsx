import Link from 'next/link'
import { NAV_ITEMS, type Role } from '@/lib/domain/role'

export function ModuleNav({ role, pathname }: { role: Role; pathname: string }) {
  return (
    <nav className="module-nav">
      {NAV_ITEMS.filter((item) => item.roles.includes(role)).map((item) => (
        <Link key={item.href} href={item.href} className={pathname === item.href ? 'active' : ''}>
          {item.label}
        </Link>
      ))}
    </nav>
  )
}
