import { useState, useEffect } from 'react'
import { Settings, X } from 'lucide-react'
import { Dropzone } from './components/Dropzone'
import { MarkdownPreview } from './components/MarkdownPreview'
import './App.css'

function App() {
  const [isProcessing, setIsProcessing] = useState(false)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [markdown, setMarkdown] = useState('')
  const [error, setError] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  
  // Settings State
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('markitdown_api_key') || '')
  const [model, setModel] = useState(() => localStorage.getItem('markitdown_model') || 'gpt-4o')
  
  // New States for Khat Mark and Json
  const [targetFormat, setTargetFormat] = useState('md')
  const [llmProvider, setLlmProvider] = useState(() => localStorage.getItem('khat_llm_provider') || 'openai')

  useEffect(() => {
    localStorage.setItem('markitdown_api_key', apiKey)
    localStorage.setItem('markitdown_model', model)
    localStorage.setItem('khat_llm_provider', llmProvider)
  }, [apiKey, model, llmProvider])

  useEffect(() => {
    let interval = null;
    if (isProcessing) {
      setElapsedTime(0);
      interval = setInterval(() => {
        setElapsedTime((prev) => prev + 1);
      }, 1000);
    } else {
      setElapsedTime(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isProcessing]);

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleFileDrop = (file) => {
    setSelectedFile(file)
    setError('')
    setMarkdown('')
  }

  const handleFormatChange = (format) => {
    setTargetFormat(format)
    setMarkdown('')
    setError('')
  }

  const handleConvert = async () => {
    if (!selectedFile) return;
    
    setIsProcessing(true)
    setError('')
    setMarkdown('')

    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('target_format', targetFormat)
    formData.append('llm_provider', llmProvider)
    
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
      if (targetFormat === 'json') {
        setMarkdown("```json\n" + JSON.stringify(data.json_data, null, 2) + "\n```")
      } else {
        setMarkdown(data.markdown)
      }
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
                <label>Provedor de IA (LLM)</label>
                <select value={llmProvider} onChange={e => setLlmProvider(e.target.value)}>
                  <option value="openai">OpenAI</option>
                  <option value="gemini">Google Gemini</option>
                </select>
              </div>

              <div className="form-group">
                <label>API Key</label>
                <input 
                  type="password" 
                  placeholder={llmProvider === 'openai' ? "sk-..." : "AIza..."} 
                  value={apiKey} 
                  onChange={e => setApiKey(e.target.value)}
                />
              </div>

              {llmProvider === 'openai' && (
                <div className="form-group">
                  <label>Modelo (Apenas OpenAI via MarkItDown)</label>
                  <select value={model} onChange={e => setModel(e.target.value)}>
                    <option value="gpt-4o">GPT-4o (Recomendado)</option>
                    <option value="gpt-4o-mini">GPT-4o Mini</option>
                    <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  </select>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <header className="header animate-fade-in">
        <div className="title-container" style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'center', gap: '2rem', width: '100%', marginBottom: '1rem' }}>
          <h1 style={{ margin: 0 }}>Khat Mark And Json</h1>
          
          <div className="format-toggle" style={{ display: 'flex', gap: '10px', background: 'rgba(255,255,255,0.1)', padding: '5px', borderRadius: '8px' }}>
            <button 
              className={`toggle-btn ${targetFormat === 'md' ? 'active' : ''}`}
              onClick={() => handleFormatChange('md')}
              style={{ padding: '5px 15px', borderRadius: '4px', border: 'none', background: targetFormat === 'md' ? '#007bff' : 'transparent', color: 'white', cursor: 'pointer' }}
            >
              Markdown
            </button>
            <button 
              className={`toggle-btn ${targetFormat === 'json' ? 'active' : ''}`}
              onClick={() => handleFormatChange('json')}
              style={{ padding: '5px 15px', borderRadius: '4px', border: 'none', background: targetFormat === 'json' ? '#007bff' : 'transparent', color: 'white', cursor: 'pointer' }}
            >
              JSON
            </button>
          </div>
        </div>
        <p>Converta qualquer documento em Markdown limpo ou JSON estruturado.</p>
      </header>

      <main className={`main-content ${markdown ? 'has-file' : ''}`}>
        <div className="left-panel">
          <Dropzone onFileDrop={handleFileDrop} isProcessing={isProcessing} selectedFile={selectedFile} elapsedTime={elapsedTime} formatTime={formatTime} />
          
          {selectedFile && (
            <button 
              onClick={handleConvert} 
              disabled={isProcessing}
              className="action-btn animate-fade-in"
              style={{
                marginTop: '1rem',
                width: '100%',
                padding: '1rem',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '1.1rem',
                fontWeight: 'bold',
                cursor: isProcessing ? 'not-allowed' : 'pointer',
                opacity: isProcessing ? 0.7 : 1,
                transition: 'all 0.2s ease',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
              }}
            >
              {isProcessing ? 'Processando...' : `Converter para ${targetFormat === 'md' ? 'Markdown' : 'JSON'}`}
            </button>
          )}

          {error && (
            <div className="error-message animate-fade-in">
              {error}
            </div>
          )}
        </div>

        {markdown && (
          <div className="right-panel">
            <MarkdownPreview content={markdown} targetFormat={targetFormat} />
          </div>
        )}
      </main>
    </div>
  )
}

export default App
