import { useState } from 'react';
import { Copy, Download, Check } from 'lucide-react';
import './MarkdownPreview.css';

export function MarkdownPreview({ content, targetFormat = 'md' }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const isJson = targetFormat === 'json';
    const blob = new Blob([content], { type: isJson ? 'application/json' : 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `markitdown-export.${isJson ? 'json' : 'md'}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="preview-container glass-panel animate-fade-in">
      <div className="preview-header">
        <h3 className="preview-title">{targetFormat === 'json' ? 'JSON Gerado' : 'Markdown Gerado'}</h3>
        <div className="preview-actions">
          <button onClick={handleCopy} className="action-btn" title={targetFormat === 'json' ? 'Copiar JSON' : 'Copiar Markdown'}>
            {copied ? <Check size={18} className="text-success" /> : <Copy size={18} />}
            <span>{copied ? 'Copiado!' : 'Copiar'}</span>
          </button>
          <button onClick={handleDownload} className="action-btn primary" title="Baixar Arquivo">
            <Download size={18} />
            <span>Baixar .{targetFormat === 'json' ? 'json' : 'md'}</span>
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
