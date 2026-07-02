import styles from './ThemeToggle.module.css'
import { useTheme } from '../../context/ThemeContext'
import { Tooltip } from 'antd'
import { SunOutlined, MoonOutlined } from '@ant-design/icons'

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()

  return (
    <Tooltip title={theme === 'light' ? '切换夜间模式' : '切换日间模式'}>
      <button
        className={styles.toggle}
        onClick={toggleTheme}
        type="button"
        aria-label={theme === 'light' ? '切换到夜间模式' : '切换到日间模式'}
      >
        {theme === 'light' ? <MoonOutlined /> : <SunOutlined />}
      </button>
    </Tooltip>
  )
}
