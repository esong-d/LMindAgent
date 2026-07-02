import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'

type Theme = 'light' | 'dark'

type ThemeContextValue = {
  theme: Theme
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

function getStoredTheme(): Theme {
  const stored = localStorage.getItem('theme')
  if (stored === 'dark' || stored === 'light') return stored
  return 'light'
}

function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme
  localStorage.setItem('theme', theme)
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(getStoredTheme)

  // Sync on mount
  useEffect(() => {
    const current = getStoredTheme()
    applyTheme(current)
    setTheme(current)
  }, [])

  // Listen for storage events from other tabs
  useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key === 'theme') {
        const newTheme = (e.newValue === 'dark' ? 'dark' : 'light') as Theme
        setTheme(newTheme)
        applyTheme(newTheme)
      }
    }
    window.addEventListener('storage', handler)
    return () => window.removeEventListener('storage', handler)
  }, [])

  const toggleTheme = useCallback(() => {
    setTheme((prev) => {
      const next = prev === 'light' ? 'dark' : 'light'
      applyTheme(next)
      return next
    })
  }, [])

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
