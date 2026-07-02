import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import ui from '../../styles/ui.module.css'
import styles from './Register.module.css'
import loginStyles from './Login.module.css'
import { ApiError } from '../../lib/apiClient'
import { register } from '../../features/auth/api'
import { setStoredAuth } from '../../features/auth/store'
import { useToast } from '../../components/Toast/ToastProvider'
import { EyeInvisibleOutlined, EyeOutlined } from '@ant-design/icons'

function errorToMessage(error: unknown) {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return '注册失败，请稍后重试'
}

export function RegisterPage() {
  const navigate = useNavigate()
  const nameRef = useRef<HTMLInputElement>(null)
  const emailRef = useRef<HTMLInputElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)
  const { showToast } = useToast()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    nameRef.current?.focus()
  }, [])

  function validate(): string | null {
    const trimmedName = name.trim()
    if (!trimmedName) return '请输入用户名'
    if (trimmedName.length < 1) return '用户名至少需要 1 个字符'
    if (trimmedName.length > 255) return '用户名不能超过 255 个字符'

    const trimmedEmail = email.trim()
    if (!trimmedEmail) return '请输入邮箱'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) return '邮箱格式不正确'

    if (!password) return '请输入密码'
    if (password.length < 8) return '密码至少需要 8 个字符'
    if (password.length > 128) return '密码不能超过 128 个字符'

    if (password !== confirmPassword) return '两次输入的密码不一致'

    return null
  }

  async function onSubmit(e: React.SyntheticEvent<HTMLFormElement, SubmitEvent>) {
    e.preventDefault()
    if (submitting) return

    const error = validate()
    if (error) {
      showToast({ type: 'error', title: '注册失败', message: error })
      return
    }

    setSubmitting(true)
    try {
      const res = await register({
        name: name.trim(),
        email: email.trim(),
        password,
        confirm_password: confirmPassword,
      })
      setStoredAuth(res)
      showToast({ type: 'success', title: '注册成功', message: '欢迎加入！' })
      navigate('/login', { replace: true })
    } catch (err) {
      showToast({ type: 'error', title: '注册失败', message: errorToMessage(err) })
    } finally {
      setSubmitting(false)
    }
  }

  const isValid =
    name.trim().length >= 1 &&
    name.trim().length <= 255 &&
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim()) &&
    password.length >= 8 &&
    password.length <= 128 &&
    confirmPassword === password

  return (
    <div className={styles.shell}>
      {/* Decorative background elements */}
      <div className={styles.bgOrb} aria-hidden="true" />
      <div className={styles.bgOrb2} aria-hidden="true" />

      <div className={styles.card}>
        {/* Decorative accent bar */}
        <div className={styles.accentBar} aria-hidden="true" />

        <div className={styles.header}>
          <div className={styles.badge}>新账号</div>
          <h1 className={styles.title}>创建账户</h1>
          <p className={styles.subtitle}>
            注册一个新账号，开始构建你的知识工作台。
          </p>
        </div>

        <form className={styles.form} onSubmit={onSubmit} noValidate aria-busy={submitting}>
          <label className={loginStyles.field}>
            <span className={loginStyles.label}>用户名</span>
            <input
              className={loginStyles.input}
              type="text"
              autoComplete="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="你的名字"
              ref={nameRef}
              required
            />
          </label>

          <label className={loginStyles.field}>
            <span className={loginStyles.label}>邮箱</span>
            <input
              className={loginStyles.input}
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              inputMode="email"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              ref={emailRef}
              required
            />
          </label>

          <label className={loginStyles.field}>
            <span className={loginStyles.label}>密码</span>
            <div className={loginStyles.passwordWrap}>
              <input
                className={`${loginStyles.input} ${loginStyles.passwordInput}`}
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="至少 8 个字符"
                ref={passwordRef}
                required
              />
              <button
                className={loginStyles.passwordToggle}
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? '隐藏密码' : '显示密码'}
              >
                {showPassword ? (
                  <EyeOutlined className={loginStyles.eyeIcon} aria-hidden="true" />
                ) : (
                  <EyeInvisibleOutlined className={loginStyles.eyeIcon} aria-hidden="true" />
                )}
              </button>
            </div>
          </label>

          <label className={loginStyles.field}>
            <span className={loginStyles.label}>确认密码</span>
            <div className={loginStyles.passwordWrap}>
              <input
                className={`${loginStyles.input} ${loginStyles.passwordInput}`}
                type={showConfirmPassword ? 'text' : 'password'}
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="再次输入密码"
                required
              />
              <button
                className={loginStyles.passwordToggle}
                type="button"
                onClick={() => setShowConfirmPassword((v) => !v)}
                aria-label={showConfirmPassword ? '隐藏确认密码' : '显示确认密码'}
              >
                {showConfirmPassword ? (
                  <EyeOutlined className={loginStyles.eyeIcon} aria-hidden="true" />
                ) : (
                  <EyeInvisibleOutlined className={loginStyles.eyeIcon} aria-hidden="true" />
                )}
              </button>
            </div>
          </label>

          <button
            className={`${ui.btn} ${ui.btnPrimary} ${loginStyles.submit} ${styles.submitOverride}`}
            type="submit"
            disabled={submitting || !isValid}
          >
            {submitting ? '注册中…' : '注册'}
          </button>
        </form>

        <p className={styles.footer}>
          已有账号？<Link to="/login" className={styles.link}>返回登录</Link>
        </p>
      </div>
    </div>
  )
}
