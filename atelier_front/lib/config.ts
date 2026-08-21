declare global {
  interface Window {
    __ATELIER_API_URL?: string
  }
}

export function getApiUrl(): string {
  if (typeof window !== 'undefined') {
    const host = window.location.hostname
    if (host === 'localhost' || host === '127.0.0.1') {
      return (process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')
    }
    if (window.__ATELIER_API_URL) {
      return window.__ATELIER_API_URL.replace(/\/$/, '')
    }
  }
  return (process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')
}
