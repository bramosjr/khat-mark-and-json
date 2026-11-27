import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Fonte servida pelo próprio app: a interface não busca nada na rede.
import '@fontsource-variable/outfit'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
