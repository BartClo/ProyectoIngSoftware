import React, { useState } from 'react';
import './report-modal.css';

interface ReportModalProps {
  conversationId: string;
  conversationTitle: string;
  onClose: () => void;
  onSubmit: (reportData: ReportData) => void;
}

export interface ReportData {
  conversationId: string;
  reportType: string;
  description: string;
}

const ReportModal: React.FC<ReportModalProps> = ({
  conversationId,
  conversationTitle: _conversationTitle,
  onClose,
  onSubmit
}) => {
  const [reportType, setReportType] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!reportType) {
      alert('Por favor, selecciona un tipo de problema.');
      return;
    }
    
    setIsSubmitting(true);
    
    const reportData: ReportData = {
      conversationId,
      reportType,
      description
    };
    
    // Pequeña pausa para mostrar el estado "Enviando..."
    setTimeout(() => {
      onSubmit(reportData);
      setIsSubmitting(false);
      onClose();
    }, 500);
  };

  return (
    <div className="report-modal-overlay" onClick={onClose}>
      <div className="report-modal-content" onClick={e => e.stopPropagation()}>
        <div className="report-modal-header">
          <h3>Reportar problema</h3>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        
          <div className="report-modal-body">
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="reportType">Tipo de problema:</label>
                <select 
                  id="reportType" 
                  value={reportType} 
                  onChange={(e) => setReportType(e.target.value)}
                  required
                >
                  <option value="">Selecciona una opción</option>
                  <option value="incorrect_information">Información incorrecta</option>
                  <option value="harmful_content">Contenido inapropiado o dañino</option>
                  <option value="system_error">Error del sistema</option>
                  <option value="slow_response">Respuestas lentas</option>
                  <option value="other">Otro problema</option>
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="description">Descripción (opcional):</label>
                <textarea 
                  id="description" 
                  value={description} 
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe el problema con más detalle..."
                  rows={4}
                  readOnly={false}
                />
              </div>            <div className="form-actions">
              <button 
                type="button" 
                className="cancel-button" 
                onClick={onClose}
              >
                Cancelar
              </button>
              <button 
                type="submit" 
                className="submit-button"
                disabled={isSubmitting || !reportType}
              >
                {isSubmitting ? 'Enviando...' : 'Enviar reporte'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ReportModal;