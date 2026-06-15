import { useState, useEffect } from 'react'
import { Settings, X } from 'lucide-react'
import { Dropzone } from './components/Dropzone'
import { MarkdownPreview } from './components/MarkdownPreview'
import './App.css'

function App() {
  const [isProcessing, setIsProcessing] = useState(false)
  const [markdown, setMarkdown] = useState('')
  const [error, setError] = useState('')
  
  // Settings State
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('markitdown_api_key') || '')
  const [model, setModel] = useState(() => localStorage.getItem('markitdown_model') || 'gpt-4o')

  useEffect(() => {
    localStorage.setItem('markitdown_api_key', apiKey)
    localStorage.setItem('markitdown_model', model)
  }, [apiKey, model])

  const handleFileDrop = async (file) => {
    setIsProcessing(true)
    setError('')
    setMarkdown('')

    const formData = new FormData()
    formData.append('file', file)
    
    // Inject LLM parameters if available
    if (apiKey.trim()) {
      formData.append('llm_api_key', apiKey.trim())
      formData.append('llm_model', model)
    }

    try {
      let headers = {}
      if (window.electronAPI && window.electronAPI.getToken) {
        const token = await window.electronAPI.getToken()
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch('http://127.0.0.1:8000/api/convert', {
        method: 'POST',
        headers: headers,
        body: formData,
      })

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || 'Erro ao processar o arquivo.')
      }

      const data = await response.json()
      setMarkdown(data.markdown)
    } catch (err) {
      console.error(err)
      setError(err.message)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="app-container">
      <button 
        className="settings-toggle action-btn" 
        onClick={() => setIsSettingsOpen(true)}
        title="Configurações (LLM)"
      >
        <Settings size={20} />
      </button>

      {/* Modal de Configurações */}
      {isSettingsOpen && (
        <div className="modal-overlay animate-fade-in">
          <div className="modal-content glass-panel">
            <div className="modal-header">
              <h2>Configurações da IA</h2>
              <button onClick={() => setIsSettingsOpen(false)} className="close-btn"><X size={20}/></button>
            </div>
            <div className="modal-body">
              <p className="modal-desc">
                Para transcrever Imagens e obter descrições ricas, o MarkItDown suporta integração com LLMs. Insira sua chave de API da OpenAI abaixo:
              </p>
              
              <div className="form-group">
                <label>OpenAI API Key</label>
                <input 
                  type="password" 
                  placeholder="sk-..." 
                  value={apiKey} 
                  onChange={e => setApiKey(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Modelo</label>
                <select value={model} onChange={e => setModel(e.target.value)}>
                  <option value="gpt-4o">GPT-4o (Recomendado)</option>
                  <option value="gpt-4o-mini">GPT-4o Mini</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      )}

      <header className="header animate-fade-in">
        <div className="title-container">
          <h1>Khat MarkItDown</h1>
        </div>
        <p>Converta qualquer documento (até mesmo imagens) em Markdown.</p>
      </header>

      <main className={`main-content ${markdown ? 'has-file' : ''}`}>
        <div className="left-panel">
          <Dropzone onFileDrop={handleFileDrop} isProcessing={isProcessing} />
          {error && (
            <div className="error-message animate-fade-in">
              {error}
            </div>
          )}
        </div>

        {markdown && (
          <div className="right-panel">
            <MarkdownPreview content={markdown} />
          </div>
        )}
      </main>
    </div>
  )
}

export default App
