import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import { AppProviders } from '@/lib/application/providers'
import './globals.css'

export const metadata: Metadata = {
  title: 'ATELIER · Content Suite',
  description: 'Un taller editorial para construir, producir y aprobar contenido de marca.',
}

export const viewport: Viewport = {
  colorScheme: 'light',
  themeColor: '#F8FAFC',
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es" className="bg-background">
      <body className="antialiased">
        <AppProviders>
          {children}
        </AppProviders>
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
