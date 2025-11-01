import React, { useEffect, useMemo, useState } from 'react';
import './users-table.css';
import ReportEditModal from './report-edit-modal';
import type { AdminReportEditData } from './report-edit-modal';
import { useAdminData } from './admin-data-context';

type ReportStatus = 'pendiente' | 'resuelto';

export interface ReportRow {
  id: string;
  docente: string;
  email: string;
  tipo: string;
  comentario: string;
  fechaEnvio: string;
  estado: ReportStatus;
  adminComentario?: string;
}

const ReportsTable: React.FC = () => {
  const { users, reports, setReports } = useAdminData();
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'todos' | ReportStatus>('todos');
  const [modalData, setModalData] = useState<AdminReportEditData | null>(null);
  const PAGE_SIZE = 8;
  const [page, setPage] = useState(1);
  useEffect(() => { setPage(1); }, [query, statusFilter]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return reports.filter(r => {
      const user = users.find(u => u.email.toLowerCase() === r.email.toLowerCase());
      const docenteName = user?.nombre?.toLowerCase() ?? r.docente.toLowerCase();
      const emailValue = user?.email?.toLowerCase() ?? r.email.toLowerCase();
      const byQuery = !q || docenteName.includes(q) || emailValue.includes(q) || r.tipo.toLowerCase().includes(q) || r.comentario.toLowerCase().includes(q);
      const byStatus = statusFilter === 'todos' || r.estado === statusFilter;
      return byQuery && byStatus;
    });
  }, [reports, query, statusFilter, users]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  useEffect(() => { if (page > totalPages) setPage(totalPages); }, [page, totalPages]);
  const pageItems = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
    return filtered.slice(start, end);
  }, [filtered, page]);

  const startEdit = (id: string) => {
    const r = reports.find(x => x.id === id);
    if (!r) return;
    setModalData({ ...r });
  };

  const handleModalSave = (data: AdminReportEditData) => {
    setReports(prev => prev.map(r => (r.id === data.id ? { ...r, ...data } : r)));
    showToast('Reporte actualizado');
    setModalData(null);
  };

  const showToast = (msg: string) => {
    const toast = document.createElement('div');
    toast.className = 'toast-notice';
    toast.textContent = msg;
    document.body.appendChild(toast);
    const showTimer = window.setTimeout(() => toast.classList.add('show'), 10);
    const hideTimer = window.setTimeout(() => toast.classList.remove('show'), 2010);
    const removeTimer = window.setTimeout(() => toast.remove(), 2350);
    return () => {
      window.clearTimeout(showTimer);
      window.clearTimeout(hideTimer);
      window.clearTimeout(removeTimer);
      toast.remove();
    };
  };

  return (
    <div className="admin-wrapper">
      <div className="admin-card">
        <div className="admin-card-header">
          <h2>Gestión de Reportes</h2>
          <div className="actions">
            <input
              className="search"
              placeholder="🔍 Buscar por docente, correo, tipo o comentario..."
              value={query}
              onChange={e => setQuery(e.target.value)}
              aria-label="Buscar reportes"
              title="Busque reportes por docente, correo, tipo o comentario"
            />
            <select 
              className="search" 
              value={statusFilter} 
              onChange={e => setStatusFilter(e.target.value as any)}
              aria-label="Filtrar por estado"
              title="Filtrar reportes según su estado"
            >
              <option value="todos">📋 Todos los estados</option>
              <option value="pendiente">⏳ Pendiente</option>
              <option value="resuelto">✓ Resuelto</option>
            </select>
          </div>
        </div>
        <div className="table-scroll">
          <table className="users-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Docente</th>
                <th>Correo</th>
                <th>Tipo</th>
                <th>Comentario</th>
                <th>Fecha envío</th>
                <th>Estado</th>
                <th style={{ width: 150 }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {pageItems.map(r => {
                const user = users.find(u => u.email.toLowerCase() === r.email.toLowerCase());
                const nombre = user?.nombre ?? r.docente;
                const email = user?.email ?? r.email;
                return (
                <tr key={r.id} className="fixed-height">
                  <td>{r.id}</td>
                  <td>{nombre}</td>
                  <td>{email}</td>
                  <td>{r.tipo}</td>
                  <td>
                    <span title={r.comentario} style={{ maxWidth: 360, display: 'inline-block', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.comentario}</span>
                  </td>
                  <td>{new Date(r.fechaEnvio).toLocaleDateString()}</td>
                  <td>
                    <span className={r.estado === 'resuelto' ? 'badge success' : 'badge'}>{r.estado === 'resuelto' ? 'Resuelto' : 'Pendiente'}</span>
                  </td>
                  <td className="row-actions">
                    <button 
                      className="small" 
                      onClick={() => startEdit(r.id)}
                      aria-label="Ver detalles del reporte"
                      title="Ver y editar detalles completos del reporte"
                    >
                      📝 Ver detalles
                    </button>
                  </td>
                </tr>
                );
              })}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8}>
                    <div className="empty-state">
                      <div className="empty-state-icon">📊</div>
                      <div className="empty-state-title">No se encontraron reportes</div>
                      <div className="empty-state-text">
                        {query || statusFilter !== 'todos' 
                          ? 'No hay reportes que coincidan con sus filtros. Intente ajustar los criterios de búsqueda.' 
                          : 'Aún no hay reportes en el sistema. Los reportes aparecerán aquí cuando los docentes los envíen.'}
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {filtered.length > 0 && (
          <div className="pagination-bar">
            <div className="pagination-info">
              <span>Mostrando {((page - 1) * PAGE_SIZE) + 1} - {Math.min(page * PAGE_SIZE, filtered.length)} de {filtered.length} reportes</span>
            </div>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <button 
                className="small" 
                onClick={() => setPage(p => Math.max(1, p - 1))} 
                disabled={page === 1}
                aria-label="Página anterior"
                title="Ir a la página anterior"
              >
                ← Anterior
              </button>
              <span className="page-indicator">Página {page} de {totalPages}</span>
              <button 
                className="small" 
                onClick={() => setPage(p => Math.min(totalPages, p + 1))} 
                disabled={page === totalPages}
                aria-label="Página siguiente"
                title="Ir a la página siguiente"
              >
                Siguiente →
              </button>
            </div>
          </div>
        )}
      </div>
      {modalData && (
        <ReportEditModal
          report={modalData}
          onClose={() => setModalData(null)}
          onSave={handleModalSave}
        />
      )}
    </div>
  );
};

export default ReportsTable;
