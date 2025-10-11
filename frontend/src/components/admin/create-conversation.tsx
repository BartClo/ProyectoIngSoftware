import React, { useMemo, useRef, useState, useEffect } from 'react';
import './create-conversation.css';
import { useAdminData } from './admin-data-context';
import { createConversationAdmin, listAdminConversations, deleteAdminConversation } from '../../lib/api';

type ConversationFile = {
  id: string;
  name: string;
  size: number;
  type: string;
};

type Conversation = {
  id: string;
  titulo: string;
  usuarios: string[];
  archivos: ConversationFile[];
  fechaCreacion: string;
};

// Directorio basado en la tabla de usuarios de administración

const acceptMime = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
  'application/msword', // .doc
  'application/vnd.openxmlformats-officedocument.presentationml.presentation', // .pptx
  'application/vnd.ms-powerpoint', // .ppt
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
  'application/vnd.ms-excel', // .xls
];

const acceptAttr = [
  '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx'
].join(',');

const CreateConversation: React.FC = () => {
  const [titulo, setTitulo] = useState('');
  const [usuarioQuery, setUsuarioQuery] = useState('');
  const [usuarios, setUsuarios] = useState<string[]>([]);
  const [archivos, setArchivos] = useState<ConversationFile[]>([]);
  const [convs, setConvs] = useState<Conversation[]>([]);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [page, setPage] = useState(1);
  // Mostrar solo 3 por página en el listado
  const PAGE_SIZE = 3;
  const [viewConv, setViewConv] = useState<Conversation | null>(null);
  const [editFilesConv, setEditFilesConv] = useState<Conversation | null>(null);
  const { users } = useAdminData();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const suggestions = useMemo(() => {
    const q = usuarioQuery.trim().toLowerCase();
    if (!q) return [] as string[];
    const directory = users.map(u => u.email.toLowerCase());
    return directory.filter(e => e.includes(q) && !usuarios.includes(e)).slice(0, 8);
  }, [usuarioQuery, usuarios, users]);

  const addUsuario = (email: string) => {
    if (!usuarios.includes(email)) setUsuarios(prev => [...prev, email]);
    setUsuarioQuery('');
  };
  const removeUsuario = (email: string) => {
    setUsuarios(prev => prev.filter(u => u !== email));
  };

  const removeArchivo = (id: string) => setArchivos(prev => prev.filter(a => a.id !== id));

  // Manejar selección de archivos desde input y guardar metadatos
  const onPickFiles = (files: FileList | null) => {
    if (!files) return;
    const next: ConversationFile[] = [];
    for (const f of Array.from(files)) {
      if (!acceptMime.includes(f.type) && !acceptAttr.split(',').some(ext => f.name.toLowerCase().endsWith(ext.trim()))) continue;
      next.push({ id: crypto.randomUUID(), name: f.name, size: f.size, type: f.type });
    }
    setArchivos(prev => [...prev, ...next]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  useEffect(() => {
    // cargar conversaciones del backend al montar
    listAdminConversations().then((list: any) => {
      if (Array.isArray(list)) setConvs(list.map((c: any) => ({ id: String(c.id), titulo: c.title, usuarios: c.users || [], archivos: (c.files || []).map((f: any) => ({ id: f.filename, name: f.filename, size: 0, type: '' })), fechaCreacion: new Date(c.created_at).toISOString() })));
    }).catch(() => {});
  }, []);

  // Permitir crear conversación incluso sin archivos
  const isValid = titulo.trim().length > 0 && usuarios.length > 0;

  const showToast = (msg: string) => {
    const toast = document.createElement('div');
    toast.className = 'toast-notice';
    toast.textContent = msg;
    document.body.appendChild(toast);
    const showTimer = window.setTimeout(() => toast.classList.add('show'), 10);
    const hideTimer = window.setTimeout(() => toast.classList.remove('show'), 2010);
    const removeTimer = window.setTimeout(() => toast.remove(), 2350);
    return () => { window.clearTimeout(showTimer); window.clearTimeout(hideTimer); window.clearTimeout(removeTimer); toast.remove(); };
  };

  const crear = () => {
    if (!isValid) {
      showToast('Faltan datos: título, usuarios o archivos');
      return;
    }
    // Preparar formulario multipart con archivos reales (si están seleccionados)
    const form = new FormData();
    form.append('title', titulo.trim());
    form.append('users', usuarios.join(','));
    const fileInput = fileInputRef.current;
    if (fileInput && fileInput.files) {
      for (const f of Array.from(fileInput.files)) form.append('files', f as File);
    }

    if (creating) return;
    setCreating(true);
    createConversationAdmin(form).then((created: any) => {
      console.log('createConversationAdmin response', created);
      showToast('La conversación se creó correctamente');
      if (Array.isArray(usuarios) && usuarios.length > 0) {
        // Avisar si el servidor no encontró algunos emails
        const returned = created?.users || [];
        const notFound = usuarios.filter(u => !returned.includes(u));
        if (notFound.length > 0) {
          alert('Advertencia: algunos usuarios no fueron encontrados en el servidor: ' + notFound.join(', '));
        }
      }
      // Insertar la conversación devuelta por el servidor al inicio de la lista
      const mapped = {
        id: String(created.id),
        titulo: created.title,
        usuarios: created.users || [],
        archivos: (created.files || []).map((f: any) => ({ id: f.filename, name: f.filename, size: 0, type: '' })),
        fechaCreacion: new Date(created.created_at).toISOString(),
      } as Conversation;
      setConvs(prev => [mapped, ...prev]);
      // limpiar formulario
      setTitulo('');
      setUsuarios([]);
      setArchivos([]);
      setUsuarioQuery('');
      setPage(1);
    }).catch((e)=>{
      console.error('create conv', e);
      alert('Error creando conversación');
    }).finally(() => setCreating(false));
  };

  const totalPages = Math.max(1, Math.ceil(convs.length / PAGE_SIZE));
  // Asegurar que la página actual no supere el total disponible
  React.useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);
  const pageItems = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
    return convs.slice(start, end);
  }, [convs, page]);

  return (
    <div className="admin-wrapper">
      <div className="admin-card">
        <div className="admin-card-header">
          <h2>Crear conversación</h2>
        </div>
        <div className="create-form">
          <label className="field-label">
            <span>Título</span>
            <input className="cell-input" value={titulo} onChange={e => setTitulo(e.target.value)} placeholder="Asunto o título de la conversación" />
          </label>

          <label className="field-label">
            <span>Usuarios (email)</span>
            <div className="user-typeahead">
              <input
                className="cell-input"
                value={usuarioQuery}
                onChange={e => setUsuarioQuery(e.target.value)}
                placeholder="Escribe para buscar y seleccionar usuarios"
              />
              {suggestions.length > 0 && (
                <div className="suggestions">
                  {suggestions.map(s => (
                    <div key={s} className="suggestion-item" onClick={() => addUsuario(s)}>
                      {s}
                    </div>
                  ))}
                </div>
              )}
            </div>
            {usuarios.length > 0 && (
              <div className="chips">
                {usuarios.map(u => (
                  <span key={u} className="chip">{u} <button onClick={() => removeUsuario(u)}>×</button></span>
                ))}
              </div>
            )}
          </label>

          <label className="field-label">
            <span>Adjuntar documentos (PDF, Word, Excel, PPT)</span>
            <input
              ref={fileInputRef}
              type="file"
              accept={acceptAttr}
              multiple
              onChange={e => onPickFiles(e.target.files)}
            />
            {archivos.length > 0 && (
              <div className="files-list">
                {archivos.map(a => (
                  <div key={a.id} className="file-row">
                    <div>
                      <strong>{a.name}</strong> <span style={{ color: '#667' }}>({Math.ceil(a.size / 1024)} KB)</span>
                    </div>
                    <button className="small" onClick={() => removeArchivo(a.id)}>Eliminar</button>
                  </div>
                ))}
              </div>
            )}
          </label>

          <div className="create-actions">
            <button className="small" onClick={() => { setTitulo(''); setUsuarios([]); setArchivos([]); setUsuarioQuery(''); }}>Cancelar</button>
            <button className="small primary" onClick={crear} disabled={!isValid}>Crear</button>
          </div>
        </div>
      </div>

      <div className="admin-card" style={{ marginTop: 16 }}>
        <div className="admin-card-header">
          <h2>Conversaciones creadas</h2>
        </div>
        <div className="table-scroll">
          <table className="users-table">
            <thead>
              <tr>
                <th>Título</th>
                <th>Usuarios</th>
                <th>Archivos</th>
                <th>Fecha</th>
                <th style={{ width: 260 }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {pageItems.map(c => (
                <tr key={c.id} className="fixed-height">
                  <td>{c.titulo}</td>
                  <td>
                    <span title={c.usuarios.join(', ')} style={{ display: 'inline-block', maxWidth: 360, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {c.usuarios.join(', ')}
                    </span>
                  </td>
                  <td>{c.archivos.length}</td>
                  <td>{new Date(c.fechaCreacion).toLocaleString()}</td>
                  <td className="row-actions" style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    <button className="small" title="Ver" onClick={() => setViewConv(c)}>Ver</button>
                    <button className="small" title="Modificar archivos" onClick={() => setEditFilesConv(c)}>Archivos</button>
                    <button className="small" title="Eliminar" disabled={deletingId === c.id} onClick={async () => {
                      if (!confirm('¿Eliminar esta conversación?')) return;
                      setDeletingId(c.id);
                      try {
                        const numId = Number(c.id);
                        console.log('Admin delete: starting', { id: c.id, numId });
                        if (!Number.isNaN(numId)) {
                          await deleteAdminConversation(numId);
                          console.log('Admin delete: deleteAdminConversation resolved for', numId);
                        }
                        // refrescar la lista desde el backend para evitar inconsistencias
                        const latest: any = await listAdminConversations();
                        console.log('Admin delete: latest from server', latest && latest.length ? latest.map((x: any) => x.id) : latest);
                        if (Array.isArray(latest)) setConvs(latest.map((c: any) => ({ id: String(c.id), titulo: c.title, usuarios: c.users || [], archivos: (c.files || []).map((f: any) => ({ id: f.filename, name: f.filename, size: 0, type: '' })), fechaCreacion: new Date(c.created_at).toISOString() })));
                      } catch (err) {
                        console.error('Error eliminando conversación', err);
                        alert('No se pudo eliminar la conversación en el servidor. Intente de nuevo.');
                      } finally {
                        setDeletingId(null);
                      }
                    }}>Eliminar</button>
                  </td>
                </tr>
              ))}
              {convs.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', color: '#666' }}>Aún no hay conversaciones</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {convs.length > 0 && (
          <div className="pagination-bar">
            <button className="small" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Anterior</button>
            <span className="page-indicator">Página {page} de {totalPages}</span>
            <button className="small" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>Siguiente</button>
          </div>
        )}
      </div>
      {viewConv && (
        <div className="report-modal-overlay" onClick={() => setViewConv(null)}>
          <div className="report-modal-content" onClick={e => e.stopPropagation()}>
            <div className="report-modal-header">
              <h3>Detalle de conversación</h3>
              <button className="close-button" onClick={() => setViewConv(null)}>×</button>
            </div>
            <div className="report-modal-body">
              <div className="form-group"><label>Título:</label><div className="detail-text">{viewConv.titulo}</div></div>
              <div className="form-group"><label>Usuarios:</label><div className="detail-text">{viewConv.usuarios.join(', ')}</div></div>
              <div className="form-group"><label>Archivos:</label>
                {viewConv.archivos.length === 0 ? (
                  <div className="detail-text">Sin archivos</div>
                ) : (
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {viewConv.archivos.map(a => (
                      <li key={a.id}>{a.name} <span style={{ color: '#667' }}>({Math.ceil(a.size / 1024)} KB)</span></li>
                    ))}
                  </ul>
                )}
              </div>
              <div className="form-group"><label>Fecha de creación:</label><div className="detail-text">{new Date(viewConv.fechaCreacion).toLocaleString()}</div></div>
            </div>
            <div className="form-actions" style={{ padding: '0 16px 16px 16px' }}>
              <button className="cancel-button" onClick={() => setViewConv(null)}>Cerrar</button>
            </div>
          </div>
        </div>
      )}

      {editFilesConv && (
        <EditFilesModal
          conv={editFilesConv}
          onClose={() => setEditFilesConv(null)}
          onSave={(files) => {
            setConvs(prev => prev.map(x => x.id === editFilesConv.id ? { ...x, archivos: files } : x));
            setEditFilesConv(null);
            showToast('Archivos actualizados');
          }}
        />
      )}
    </div>
  );
};

export default CreateConversation;

// Modal embebido para editar archivos de una conversación
const EditFilesModal: React.FC<{
  conv: Conversation;
  onClose: () => void;
  onSave: (files: ConversationFile[]) => void;
}> = ({ conv, onClose, onSave }) => {
  const [files, setFiles] = useState<ConversationFile[]>(conv.archivos);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [uploading, setUploading] = useState(false);

  const onPick = (fl: FileList | null) => {
    if (!fl) return;
    const next: ConversationFile[] = [];
    for (const f of Array.from(fl)) {
      if (!acceptMime.includes(f.type) && !acceptAttr.split(',').some(ext => f.name.toLowerCase().endsWith(ext.trim()))) continue;
      next.push({ id: crypto.randomUUID(), name: f.name, size: f.size, type: f.type });
    }
    setFiles(prev => [...prev, ...next]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const remove = (id: string) => setFiles(prev => prev.filter(a => a.id !== id));

  const doSave = async () => {
    // If the user selected files in the input, upload them to the server
    if (fileInputRef.current && fileInputRef.current.files && fileInputRef.current.files.length > 0) {
      setUploading(true);
      try {
        const form = new FormData();
        for (const f of Array.from(fileInputRef.current.files)) form.append('files', f as File);
        const resp: any = await (await import('../../lib/api')).uploadConversationAttachments(Number(conv.id), form);
        // Refresh list from server
        const latest: any = await (await import('../../lib/api')).listAdminConversations();
        if (Array.isArray(latest)) {
          const found = latest.find((x: any) => String(x.id) === String(conv.id));
          const newFiles = (found?.files || []).map((f: any) => ({ id: f.filename, name: f.filename, size: 0, type: '' }));
          onSave(newFiles);
        } else {
          onSave(files);
        }
      } catch (e) {
        console.error('Error uploading attachments', e);
        alert('No se pudieron subir los archivos. Intenta de nuevo.');
      } finally {
        setUploading(false);
        onClose();
      }
      return;
    }

    // No new files to upload — just save metadata locally
    onSave(files);
    onClose();
  };

  return (
    <div className="report-modal-overlay" onClick={onClose}>
      <div className="report-modal-content" onClick={e => e.stopPropagation()}>
        <div className="report-modal-header">
          <h3>Modificar archivos</h3>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        <div className="report-modal-body">
          <div className="form-group">
            <label>Adjuntar documentos (PDF, Word, Excel, PPT)</label>
            <input ref={fileInputRef} type="file" multiple accept={acceptAttr} onChange={e => onPick(e.target.files)} />
          </div>
          <div className="files-list">
            {files.length === 0 ? (
              <div className="detail-text">No hay archivos</div>
            ) : files.map(a => (
              <div key={a.id} className="file-row">
                <div>
                  <strong>{a.name}</strong> <span style={{ color: '#667' }}>({Math.ceil(a.size / 1024)} KB)</span>
                </div>
                <button className="small" onClick={() => remove(a.id)}>Eliminar</button>
              </div>
            ))}
          </div>
        </div>
        <div className="form-actions" style={{ padding: '0 16px 16px 16px' }}>
          <button className="cancel-button" onClick={onClose}>Cancelar</button>
          <button className="submit-button" disabled={uploading} onClick={doSave}>{uploading ? 'Subiendo...' : 'Guardar'}</button>
        </div>
      </div>
    </div>
  );
};
