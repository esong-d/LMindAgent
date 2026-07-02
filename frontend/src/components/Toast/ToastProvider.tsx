import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from 'react'
import styles from './ToastProvider.module.css'
import errorIcon from '../../assets/toast/error.svg'
import successIcon from '../../assets/toast/success.svg'
import warningIcon from '../../assets/toast/warning.svg'

export type ToastType = 'info' | 'success' | 'warn' | 'error'

export type ToastOptions = {
  type?: ToastType
  title?: string
  message: string
  durationMs?: number
  dismissible?: boolean
}

type ToastItem = Required<Pick<ToastOptions, 'message'>> &
  Pick<ToastOptions, 'title'> & {
    id: string
    type: ToastType
    dismissible: boolean
    role: 'status' | 'alert'
  }

type ToastContextValue = {
  showToast: (options: ToastOptions) => void
  dismissToast: (id: string) => void
  clearToasts: () => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

function randomId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID()
  return `${Date.now()}_${Math.random().toString(16).slice(2)}`
}

const iconSrcByType: Record<ToastType, string> = {
  info: warningIcon,
  success: successIcon,
  warn: warningIcon,
  error: errorIcon,
}

function defaultTitle(type: ToastType) {
  switch (type) {
    case 'success':
      return '成功'
    case 'warn':
      return '提示'
    case 'error':
      return '错误'
    default:
      return '提示'
  }
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const timeoutsRef = useRef<Map<string, number>>(new Map())
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const dismissToast = useCallback((id: string) => {
    const timeoutId = timeoutsRef.current.get(id)
    if (timeoutId) window.clearTimeout(timeoutId)
    timeoutsRef.current.delete(id)
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const clearToasts = useCallback(() => {
    for (const timeoutId of timeoutsRef.current.values()) window.clearTimeout(timeoutId)
    timeoutsRef.current.clear()
    setToasts([])
  }, [])

  const showToast = useCallback(
    (options: ToastOptions) => {
      const type = options.type ?? 'info'
      const durationMs = options.durationMs ?? (type === 'error' ? 4000 : 2500)
      const dismissible = options.dismissible ?? true
      const id = randomId()

      const role: ToastItem['role'] = type === 'error' ? 'alert' : 'status'

      setToasts((prev) => {
        const next: ToastItem = {
          id,
          type,
          title: options.title,
          message: options.message,
          dismissible,
          role,
        }
        return [next, ...prev].slice(0, 3)
      })

      if (durationMs > 0) {
        const timeoutId = window.setTimeout(() => dismissToast(id), durationMs)
        timeoutsRef.current.set(id, timeoutId)
      }
    },
    [dismissToast],
  )

  const value = useMemo<ToastContextValue>(() => ({ showToast, dismissToast, clearToasts }), [showToast, dismissToast, clearToasts])

  return (
    <ToastContext.Provider value={value}>
      {children}
      {toasts.length ? (
        <div className={styles.viewport} aria-live="polite" aria-relevant="additions removals">
          {toasts.map((t) => (
            <div key={t.id} className={[styles.toast, styles[t.type]].join(' ')} role={t.role}>
              <div className={styles.iconWrap} aria-hidden="true">
                <img className={styles.icon} src={iconSrcByType[t.type]} alt="" />
              </div>
              <div className={styles.body}>
                <div className={styles.header}>
                  <div className={styles.title}>{t.title ?? defaultTitle(t.type)}</div>
                  {t.dismissible ? (
                    <button className={styles.close} type="button" onClick={() => dismissToast(t.id)} aria-label="关闭提示">
                      <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                        <path
                          fill="currentColor"
                          d="M18.3 5.7a1 1 0 0 0-1.4 0L12 10.6 7.1 5.7A1 1 0 1 0 5.7 7.1l4.9 4.9-4.9 4.9a1 1 0 1 0 1.4 1.4l4.9-4.9 4.9 4.9a1 1 0 0 0 1.4-1.4L13.4 12l4.9-4.9a1 1 0 0 0 0-1.4Z"
                        />
                      </svg>
                    </button>
                  ) : null}
                </div>
                <div className={styles.message}>{t.message}</div>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}

