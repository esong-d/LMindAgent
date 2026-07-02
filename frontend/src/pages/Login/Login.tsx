import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import ui from '../../styles/ui.module.css'
import styles from './Login.module.css'
import { ApiError } from '../../lib/apiClient'
import { login } from '../../features/auth/api'
import { setStoredAuth } from '../../features/auth/store'
import { useToast } from '../../components/Toast/ToastProvider'
import { EyeInvisibleOutlined, EyeOutlined } from '@ant-design/icons'

function errorToMessage(error: unknown) {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return '登录失败，请稍后重试'
}

function sanitizeRedirectTo(value: unknown) {
  if (typeof value !== 'string') return '/'
  const trimmed = value.trim()
  if (!trimmed.startsWith('/')) return '/'
  if (trimmed.startsWith('//')) return '/'
  if (trimmed.startsWith('/login')) return '/'
  return trimmed
}

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const emailRef = useRef<HTMLInputElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)
  const { showToast } = useToast()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const redirectTo = useMemo(() => {
    const state = location.state as { from?: string } | null
    return sanitizeRedirectTo(state?.from)
  }, [location.state])

  useEffect(() => {
    emailRef.current?.focus()
  }, [])

  async function onSubmit(e: React.SyntheticEvent<HTMLFormElement, SubmitEvent>) {
    e.preventDefault()
    if (submitting) return

    const trimmedEmail = email.trim()
    if (!trimmedEmail) {
      showToast({ type: 'error', title: '登录失败', message: '请输入邮箱' })
      emailRef.current?.focus()
      return
    }
    if (!password) {
      showToast({ type: 'error', title: '登录失败', message: '请输入密码' })
      passwordRef.current?.focus()
      return
    }

    setSubmitting(true)
    try {
      const res = await login({ email: trimmedEmail, password })
      setStoredAuth(res)
      showToast({ type: 'success', title: '登录成功', message: '欢迎回来！' })
      navigate(redirectTo || '/home', { replace: true })
    } catch (err) {
      showToast({ type: 'error', title: '登录失败', message: errorToMessage(err) })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className={styles.shell}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h1 className={styles.title}>登录</h1>
          <p className={styles.subtitle}>使用你的账号登录工作台。</p>
        </div>

        <form className={styles.form} onSubmit={onSubmit} noValidate aria-busy={submitting}>
          <label className={styles.field}>
            <span className={styles.label}>邮箱</span>
            <input
              className={styles.input}
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
              }}
              placeholder="user@example.com"
              inputMode="email"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              ref={emailRef}
              required
            />
          </label>

          <label className={styles.field}>
            <span className={styles.label}>密码</span>
            <div className={styles.passwordWrap}>
              <input
                className={`${styles.input} ${styles.passwordInput}`}
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value)
                }}
                placeholder="请输入密码"
                ref={passwordRef}
                required
              />
              <button
                className={styles.passwordToggle}
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? '隐藏密码' : '显示密码'}
              >
                {showPassword ? (
                  <EyeOutlined className={styles.eyeIcon} aria-hidden="true" />
                ) : (
                  <EyeInvisibleOutlined className={styles.eyeIcon} aria-hidden="true" />
                )}
              </button>
            </div>
          </label>

          <button
            className={`${ui.btn} ${ui.btnPrimary} ${styles.submit}`}
            type="submit"
            disabled={submitting || !email.trim() || !password}
          >
            {submitting ? '登录中…' : '登录'}
          </button>
        </form>

        <p className={styles.footer}>
          还没有账号？<Link to="/register" className={styles.registerLink}>立即注册</Link>
        </p>
      </div>
    </div>
  )
}
