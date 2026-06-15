import { useState } from 'react';
import { Copy, Download, Check } from 'lucide-react';
import './MarkdownPreview.css';

export function MarkdownPreview({ content }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'markitdown-export.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="preview-container glass-panel animate-fade-in">
      <div className="preview-header">
        <h3 className="preview-title">Markdown Gerado</h3>
        <div className="preview-actions">
          <button onClick={handleCopy} className="action-btn" title="Copiar Markdown">
            {copied ? <Check size={18} className="text-success" /> : <Copy size={18} />}
            <span>{copied ? 'Copiado!' : 'Copiar'}</span>
          </button>
          <button onClick={handleDownload} className="action-btn primary" title="Baixar Arquivo">
            <Download size={18} />
            <span>Baixar .md</span>
          </button>
        </div>
      </div>
      <div className="preview-content-wrapper">
        <pre className="preview-content">
          <code>{content}</code>
        </pre>
      </div>
    </div>
  );
}
