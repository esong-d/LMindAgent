import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import 'antd/dist/reset.css'
import App from './App.tsx'

// Anti-flicker: set theme attribute before first paint
const storedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
const theme = storedTheme || 'light'
document.documentElement.dataset.theme = theme
document.documentElement.classList.add('preload')
window.addEventListener('load', () => {
  document.documentElement.classList.remove('preload')
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
