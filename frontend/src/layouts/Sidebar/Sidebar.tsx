import { useEffect, useMemo, useRef, useState } from 'react'
import styles from './Sidebar.module.css'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { navItems } from '../../router/nav'
import { clearStoredAuth, getStorageAuth } from '../../features/auth/store'
import { logout } from '../../features/auth/api'
import { SettingOutlined, LogoutOutlined } from '@ant-design/icons'
import { useToast } from '../../components/Toast/ToastProvider'

export function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const userInfo = getStorageAuth()
  const { showToast } = useToast()
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({ evaluation: true })
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  // 获取不到跳转登录
  if (!userInfo || userInfo === null) {
    navigate('/login', { replace: true })
  }

  // 点击外部关闭菜单
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    if (menuOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [menuOpen])

  async function handleLogout() {
    try {
      await logout()
    } catch {
      // 即使接口出错也清除本地状态
    }
    clearStoredAuth()
    showToast({ type: 'success', title: '已退出', message: '已退出登录' })
    navigate('/login', { replace: true })
  }

  const isGroupActive = useMemo(
    () => (path: string, childPaths: string[] = []) =>
      location.pathname === path ||
      location.pathname.startsWith(`${path}/`) ||
      childPaths.some((item) => location.pathname === item || location.pathname.startsWith(`${item}/`)),
    [location.pathname],
  )

  return (
    <aside className={styles.sidebar}>
      <div className={styles.section}>
        {navItems.map((item) => {
          if (!item.children?.length) {
            return (
              <NavLink
                key={item.key}
                className={({ isActive }) =>
                  [styles.item, isActive ? styles.itemActive : ''].filter(Boolean).join(' ')
                }
                to={item.path}
                end={item.end}
              >
                {item.icon ? <span className={styles.itemIcon}>{item.icon}</span> : null}
                {item.label}
              </NavLink>
            )
          }

          const active = isGroupActive(item.path, item.children.map((child) => child.path))
          const open = openGroups[item.key] ?? active

          return (
            <div key={item.key} className={styles.group}>
              <button
                type="button"
                className={[styles.groupTrigger, active ? styles.groupTriggerActive : ''].filter(Boolean).join(' ')}
                onClick={() => setOpenGroups((prev) => ({ ...prev, [item.key]: !open }))}
              >
                {item.icon ? <span className={styles.groupTriggerIcon}>{item.icon}</span> : null}
                <span className={styles.groupTriggerLabel}>{item.label}</span>
                <span className={[styles.groupChevron, open ? styles.groupChevronOpen : ''].filter(Boolean).join(' ')}>
                  ▾
                </span>
              </button>

              {open ? (
                <div className={styles.groupChildren}>
                  {item.children.map((child) => (
                    <NavLink
                      key={child.key}
                      className={({ isActive }) =>
                        [styles.subItem, isActive ? styles.subItemActive : ''].filter(Boolean).join(' ')
                      }
                      to={child.path}
                      end={child.end}
                    >
                      {child.icon ? <span className={styles.subItemIcon}>{child.icon}</span> : null}
                      {child.label}
                    </NavLink>
                  ))}
                </div>
              ) : null}
            </div>
          )
        })}
      </div>

      <div className={styles.footer} ref={menuRef}>
        {/* 设置菜单 */}
        {menuOpen ? (
          <div className={styles.menu}>
            <button
              type="button"
              className={styles.menuItem}
              onClick={() => {
                setMenuOpen(false)
                handleLogout()
              }}
            >
              <LogoutOutlined className={styles.menuItemIconDanger} />
              退出登录
            </button>
          </div>
        ) : null}

        <div className={styles.user}>
          <div className={styles.avatar}>{userInfo?.name.slice(0, 1)}</div>
          <div className={styles.userMeta}>
            <div className={styles.userName}>{userInfo?.name}</div>
            <div className={styles.userEmail}>{userInfo?.email}</div>
          </div>
          <button
            type="button"
            className={styles.settingsBtn}
            onClick={() => setMenuOpen((v) => !v)}
            aria-label="设置"
          >
            <SettingOutlined className={styles.settingsIcon} />
          </button>
        </div>
      </div>
    </aside>
  )
}
