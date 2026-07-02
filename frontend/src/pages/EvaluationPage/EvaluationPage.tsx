import { Outlet } from 'react-router-dom'
import styles from './EvaluationPage.module.css'

export function EvaluationPage() {
  return (
    <div className={styles.page}>
      <div className={styles.content}>
        <Outlet />
      </div>
    </div>
  )
}
