import { useCallback, useState } from 'react';
import { Upload } from 'lucide-react';
import './Dropzone.css';

export function Dropzone({ onFileDrop, isProcessing }) {
  const [isDragActive, setIsDragActive] = useState(false);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileDrop(e.dataTransfer.files[0]);
    }
  }, [onFileDrop]);

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileDrop(e.target.files[0]);
    }
  };

  return (
    <div className="dropzone-wrapper animate-fade-in">
      <div 
        className={`dropzone-area glass-panel ${isDragActive ? 'drag-active' : ''} ${isProcessing ? 'processing' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input 
          type="file" 
          id="file-upload" 
          className="file-input" 
          onChange={handleChange} 
          disabled={isProcessing}
        />
        <label htmlFor="file-upload" className="dropzone-content">
          {isProcessing ? (
            <div className="processing-state">
              <div className="spinner"></div>
              <p>Processando com IA...</p>
            </div>
          ) : (
            <>
              <div className="icon-container">
                <Upload size={48} className="upload-icon" />
              </div>
              <h3>Arraste e solte o arquivo aqui</h3>
              <p>PDF, DOCX, XLSX, Imagens, Áudio ou HTML</p>
              <span className="browse-btn">Procurar Arquivo</span>
            </>
          )}
        </label>
      </div>
    </div>
  );
}
