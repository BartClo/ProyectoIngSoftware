import React, { useState } from 'react';
import '../chat/reporte-model/report-modal.css';

type ReportStatus = 'pendiente' | 'resuelto';

export interface AdminReportEditData {
  id: string;
  docente: string;
  email: string;
  tipo: string;
  comentario: string;
  fechaEnvio: string;
  estado: ReportStatus;
  adminComentario?: string;
}

interface ReportEditModalProps {
  report: AdminReportEditData;
  onClose: () => void;
  onSave: (data: AdminReportEditData) => void;
}

const ReportEditModal: React.FC<ReportEditModalProps> = ({ report, onClose, onSave }) => {
  const [tipo, setTipo] = useState(report.tipo);
  const [estado, setEstado] = useState<ReportStatus>(report.estado);
  const [adminComentario, setAdminComentario] = useState(report.adminComentario ?? '');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setTimeout(() => {
      onSave({ ...report, tipo, estado, adminComentario });
      setIsSubmitting(false);
      onClose();
    }, 200);
  };

  return (
    <div className="report-modal-overlay" onClick={onClose}>
      <div className="report-modal-content" onClick={e => e.stopPropagation()}>
        <div className="report-modal-header">
          <h3>Editar reporte</h3>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        <div className="report-modal-body">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>ID del reporte:</label>
              <div className="detail-text">{report.id}</div>
            </div>
            <div className="form-group">
              <label>Docente:</label>
              <div className="detail-text">{report.docente}</div>
            </div>
            <div className="form-group">
              <label>Correo del docente:</label>
              <div className="detail-text">{report.email}</div>
            </div>
            <div className="form-group">
              <label>Tipo de problema:</label>
              <select value={tipo} onChange={e => setTipo(e.target.value)} required>
                <option value="Información incorrecta">Información incorrecta</option>
                <option value="Contenido inapropiado">Contenido inapropiado</option>
                <option value="Error del sistema">Error del sistema</option>
                <option value="Respuestas lentas">Respuestas lentas</option>
                <option value="Otro problema">Otro problema</option>
              </select>
            </div>
            <div className="form-group">
              <label>Comentario (usuario):</label>
              <div className="detail-text">{report.comentario}</div>
            </div>
            <div className="form-group">
              <label>Fecha de envío:</label>
              <div className="detail-text">{new Date(report.fechaEnvio).toLocaleDateString()}</div>
            </div>
            <div className="form-group">
              <label>Estado:</label>
              <select value={estado} onChange={e => setEstado(e.target.value as ReportStatus)} required>
                <option value="pendiente">Pendiente</option>
                <option value="resuelto">Resuelto</option>
              </select>
            </div>
            <div className="form-group">
              <label>Comentario de solución (admin):</label>
              <textarea
                value={adminComentario}
                onChange={e => setAdminComentario(e.target.value)}
                placeholder="Describe la solución aplicada..."
                rows={4}
              />
            </div>
            <div className="form-actions">
              <button type="button" className="cancel-button" onClick={onClose}>Cancelar</button>
              <button type="submit" className="submit-button" disabled={isSubmitting}>Guardar</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ReportEditModal;