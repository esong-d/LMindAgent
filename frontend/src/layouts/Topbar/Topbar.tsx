import styles from './Topbar.module.css'
import ui from '../../styles/ui.module.css'
import brainLogo from '../../assets/brain.png'
import { useNavigate } from 'react-router-dom'
import { ThemeToggle } from '../../components/ThemeToggle/ThemeToggle'

type TopbarProps = {
  productName?: string
}

export function Topbar({ productName = 'LMindAgent' }: TopbarProps) {
  const navigate = useNavigate()

  return (
    <header className={styles.topbar}>
      <div className={styles.left}>
        <img className={styles.logo} src={brainLogo} alt="logo" />
        <div className={styles.product}>{productName}</div>
      </div>
      <div className={styles.spacer} />
      <div className={styles.right}>
        <ThemeToggle />
        <button className={`${ui.btn} ${ui.btnGhost}`} type="button" onClick={() => navigate('/documents?action=upload')}>
          上传
        </button>
        <button className={`${ui.btn} ${ui.btnPrimary}`} type="button" onClick={() => navigate('/knowledge?action=create')}>
          新建知识库
        </button>
      </div>
    </header>
  )
}
