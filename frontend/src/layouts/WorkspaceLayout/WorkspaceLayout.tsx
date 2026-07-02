import { Outlet, useLocation } from 'react-router-dom'
import { ContextPanel } from '../ContextPanel/ContextPanel'
import { Sidebar } from '../Sidebar/Sidebar'
import { Topbar } from '../Topbar/Topbar'
import styles from './WorkspaceLayout.module.css'

export function WorkspaceLayout() {
  const location = useLocation()
  // const showContextPanel = location.pathname === '/chat'
  const showContextPanel = false
  const lockMainScroll =
    location.pathname === '/tasks' ||
    location.pathname === '/knowledge' ||
    location.pathname.startsWith('/evaluation')

  return (
    <div className={styles.shell}>
      <Topbar />

      <div className={[styles.body, showContextPanel ? styles.bodyWithPanel : ''].filter(Boolean).join(' ')}>
        <div className={styles.sidebarSlot}>
          <Sidebar />
        </div>

        <main className={[styles.main, lockMainScroll ? styles.mainLocked : ''].filter(Boolean).join(' ')}>
          <Outlet />
        </main>

        {showContextPanel ? (
          <div className={styles.rightSlot}>
            <ContextPanel />
          </div>
        ) : null}
      </div>
    </div>
  )
}
