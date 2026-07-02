import { RouterProvider } from 'react-router-dom'
import { router } from './router/router'
import { ToastProvider } from './components/Toast/ToastProvider'
import { ThemeProvider } from './context/ThemeContext'
import { AntdConfig } from './context/AntdConfig'

function App() {
  return (
    <ThemeProvider>
      <AntdConfig>
        <ToastProvider>
          <RouterProvider router={router} />
        </ToastProvider>
      </AntdConfig>
    </ThemeProvider>
  )
}

export default App
