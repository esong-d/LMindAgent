import { ConfigProvider, theme as antdTheme } from 'antd'
import type { ReactNode } from 'react'
import { useTheme } from './ThemeContext'

export function AntdConfig({ children }: { children: ReactNode }) {
  const { theme } = useTheme()

  return (
    <ConfigProvider
      theme={{
        algorithm: theme === 'dark' ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
      }}
    >
      {children}
    </ConfigProvider>
  )
}
