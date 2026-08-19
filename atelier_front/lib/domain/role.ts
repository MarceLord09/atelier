export type Role = 'CREATOR' | 'APPROVER_A' | 'APPROVER_B'

export const ROLE_LABEL: Record<Role, string> = {
  CREATOR: 'Creador',
  APPROVER_A: 'Aprobador A',
  APPROVER_B: 'Aprobador B',
}

export const NAV_ITEMS: { href: string; label: string; roles: Role[] }[] = [
  { href: '/dna', label: '01 / DNA', roles: ['CREATOR'] },
  { href: '/prensa', label: '02 / PRENSA', roles: ['CREATOR'] },
  { href: '/mesa', label: '03A / MESA', roles: ['APPROVER_A'] },
  { href: '/vision', label: '03B / VISIÓN', roles: ['APPROVER_B'] },
]

export function homePath(role: Role): string {
  if (role === 'CREATOR') return '/dna'
  if (role === 'APPROVER_A') return '/mesa'
  return '/vision'
}

export function canAccess(role: Role, href: string): boolean {
  if (href === '/ayuda' || href === '/configuracion') return true
  return NAV_ITEMS.some((item) => item.href === href && item.roles.includes(role))
}
