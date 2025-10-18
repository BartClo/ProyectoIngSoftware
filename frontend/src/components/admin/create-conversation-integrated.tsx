import React, { useMemo, useRef, useState, useEffect } from 'react';
import './create-conversation.css';
import { useAdminData } from './admin-data-context';
import { 
  createConversationAdmin, 
  listAdminConversations, 
  deleteAdminConversation,
  uploadConversationAttachments,
  // APIs RAG
  createChatbot,
  listUserChatbots,
  deleteChatbot,
  updateChatbot,
  uploadDocuments,
  listChatbotDocuments,
  deleteChatbotDocument,
  processDocuments,
  getDocumentStatus,
  grantUserAccess,
  listChatbotUsers,
  revokeChatbotAccess,
  getChatbotStats
} from '../../lib/api';

// ===== TIPOS =====
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

type Chatbot = {
  id: number;
  title: string;
  description?: string;
  created_by: number;
  pinecone_index_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  documents_count: number;
  users_count: number;
};

type ChatbotDocument = {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  chunks_count: number;
  is_processed: boolean;
  processed_at?: string;
  uploaded_at: string;
  uploader_email?: string;
};

type TabType = 'conversaciones' | 'chatbots';

// ===== CONSTANTES =====
const acceptMime = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
  'application/msword', // .doc
  'application/vnd.openxmlformats-officedocument.presentationml.presentation', // .pptx
  'application/vnd.ms-powerpoint', // .ppt
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
  'application/vnd.ms-excel', // .xls
];

const acceptAttr = '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx';

const PAGE_SIZE = 3;

// ===== COMPONENTE PRINCIPAL =====
const CreateConversation: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('conversaciones');
  const { users } = useAdminData();

  // Estados para conversaciones
  const [titulo, setTitulo] = useState('');
  const [usuarioQuery, setUsuarioQuery] = useState('');
  const [usuarios, setUsuarios] = useState<string[]>([]);
  const [archivos, setArchivos] = useState<ConversationFile[]>([]);
  const [convs, setConvs] = useState<Conversation[]>([]);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [page, setPage] = useState(1);
  const [viewConv, setViewConv] = useState<Conversation | null>(null);
  const [editFilesConv, setEditFilesConv] = useState<Conversation | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Estados para chatbots
  const [chatbotTitle, setChatbotTitle] = useState('');
  const [chatbotDescription, setChatbotDescription] = useState('');
  const [chatbots, setChatbots] = useState<Chatbot[]>([]);
  const [selectedChatbot, setSelectedChatbot] = useState<Chatbot | null>(null);
  const [chatbotDocuments, setChatbotDocuments] = useState<ChatbotDocument[]>([]);
  const [creatingChatbot, setCreatingChatbot] = useState(false);
  const [uploadingDocs, setUploadingDocs] = useState(false);
  const [processingDocs, setProcessingDocs] = useState(false);
  const [deletingChatbot, setDeletingChatbot] = useState<number | null>(null);
  const chatbotFileInputRef = useRef<HTMLInputElement | null>(null);

  // Estados compartidos
  const [toasts, setToasts] = useState<{id: string, message: string, show: boolean}[]>([]);

  // ===== UTILIDADES =====
  const showToast = (message: string) => {
    const id = crypto.randomUUID();
    const toast = { id, message, show: false };
    setToasts(prev => [...prev, toast]);
    const showTimer = window.setTimeout(() => setToasts(prev => prev.map(t => t.id === id ? {...t, show: true} : t)), 100);
    const hideTimer = window.setTimeout(() => setToasts(prev => prev.map(t => t.id === id ? {...t, show: false} : t)), 3000);
    const removeTimer = window.setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3500);
    return () => { 
      window.clearTimeout(showTimer); 
      window.clearTimeout(hideTimer); 
      window.clearTimeout(removeTimer);
      setToasts(prev => prev.filter(t => t.id !== id));
    };
  };

  // ===== LÓGICA CONVERSACIONES =====
  const allEmails = Array.from(new Set(users.map((u: any) => u.email).filter(Boolean)));
  const emailSuggestions = allEmails.filter(e => e.toLowerCase().includes(usuarioQuery.toLowerCase()) && !usuarios.includes(e));
  const isValidConv = titulo.trim() && usuarios.length > 0;

  const addUsuario = (email: string) => {
    if (!usuarios.includes(email)) {
      setUsuarios(prev => [...prev, email]);
      setUsuarioQuery('');
    }
  };

  const removeUsuario = (email: string) => setUsuarios(prev => prev.filter(u => u !== email));

  const onPickArchivos = (fl: FileList | null) => {
    if (!fl) return;
    const next: ConversationFile[] = [];
    for (const f of Array.from(fl)) {
      if (!acceptMime.includes(f.type) && !acceptAttr.split(',').some(ext => f.name.toLowerCase().endsWith(ext.trim()))) continue;
      next.push({ id: crypto.randomUUID(), name: f.name, size: f.size, type: f.type });
    }
    setArchivos(prev => [...prev, ...next]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeArchivo = (id: string) => setArchivos(prev => prev.filter(a => a.id !== id));

  const crearConversacion = async () => {
    if (!isValidConv) return;
    setCreating(true);
    
    try {
      const form = new FormData();
      form.append('title', titulo.trim());
      form.append('users', usuarios.join(','));
      
      // Agregar archivos reales si están seleccionados
      const fileInput = fileInputRef.current;
      if (fileInput && fileInput.files) {
        for (const f of Array.from(fileInput.files)) {
          form.append('files', f as File);
        }
      }

      const created: any = await createConversationAdmin(form);
      showToast('Conversación creada correctamente');
      
      // Agregar a la lista
      const mapped = {
        id: String(created.id),
        titulo: created.title,
        usuarios: created.users || [],
        archivos: (created.files || []).map((f: any) => ({ id: f.filename, name: f.filename, size: 0, type: '' })),
        fechaCreacion: new Date(created.created_at).toISOString(),
      } as Conversation;
      setConvs(prev => [mapped, ...prev]);
      
      // Limpiar formulario
      setTitulo('');
      setUsuarios([]);
      setArchivos([]);
      setUsuarioQuery('');
      setPage(1);
    } catch (e) {
      console.error('Error creando conversación:', e);
      showToast('Error creando conversación');
    } finally {
      setCreating(false);
    }
  };

  // ===== LÓGICA CHATBOTS =====
  const isValidChatbot = chatbotTitle.trim().length > 0;

  const crearChatbot = async () => {
    if (!isValidChatbot) return;
    setCreatingChatbot(true);
    
    try {
      const chatbot: Chatbot = await createChatbot({
        title: chatbotTitle.trim(),
        description: chatbotDescription.trim() || undefined
      });
      
      setChatbots(prev => [chatbot, ...prev]);
      showToast('Chatbot creado correctamente');
      
      // Limpiar formulario
      setChatbotTitle('');
      setChatbotDescription('');
    } catch (e) {
      console.error('Error creando chatbot:', e);
      showToast('Error creando chatbot');
    } finally {
      setCreatingChatbot(false);
    }
  };

  const eliminarChatbot = async (chatbotId: number) => {
    if (!confirm('¿Eliminar este chatbot? Se perderán todos sus documentos y configuración.')) return;
    setDeletingChatbot(chatbotId);
    
    try {
      await deleteChatbot(chatbotId);
      setChatbots(prev => prev.filter(c => c.id !== chatbotId));
      if (selectedChatbot?.id === chatbotId) {
        setSelectedChatbot(null);
        setChatbotDocuments([]);
      }
      showToast('Chatbot eliminado correctamente');
    } catch (e) {
      console.error('Error eliminando chatbot:', e);
      showToast('Error eliminando chatbot');
    } finally {
      setDeletingChatbot(null);
    }
  };

  const seleccionarChatbot = async (chatbot: Chatbot) => {
    setSelectedChatbot(chatbot);
    
    try {
      const docs: ChatbotDocument[] = await listChatbotDocuments(chatbot.id);
      setChatbotDocuments(docs);
    } catch (e) {
      console.error('Error cargando documentos:', e);
      setChatbotDocuments([]);
    }
  };

  const subirDocumentos = async (files: FileList | null) => {
    if (!files || !selectedChatbot) return;
    setUploadingDocs(true);
    
    try {
      const uploadedDocs: ChatbotDocument[] = await uploadDocuments(selectedChatbot.id, files);
      setChatbotDocuments(prev => [...uploadedDocs, ...prev]);
      showToast(`${uploadedDocs.length} documento(s) subido(s) correctamente`);
      
      if (chatbotFileInputRef.current) {
        chatbotFileInputRef.current.value = '';
      }
    } catch (e) {
      console.error('Error subiendo documentos:', e);
      showToast('Error subiendo documentos');
    } finally {
      setUploadingDocs(false);
    }
  };

  const procesarDocumentos = async () => {
    if (!selectedChatbot) return;
    setProcessingDocs(true);
    
    try {
      await processDocuments(selectedChatbot.id);
      showToast('Procesamiento de documentos iniciado. Esto puede tomar unos minutos.');
      
      // Recargar documentos para ver el estado actualizado
      setTimeout(async () => {
        try {
          const docs: ChatbotDocument[] = await listChatbotDocuments(selectedChatbot.id);
          setChatbotDocuments(docs);
        } catch (e) {
          console.error('Error actualizando documentos:', e);
        }
      }, 2000);
    } catch (e) {
      console.error('Error procesando documentos:', e);
      showToast('Error iniciando procesamiento');
    } finally {
      setProcessingDocs(false);
    }
  };

  const eliminarDocumento = async (docId: number) => {
    if (!selectedChatbot || !confirm('¿Eliminar este documento?')) return;
    
    try {
      await deleteChatbotDocument(selectedChatbot.id, docId);
      setChatbotDocuments(prev => prev.filter(d => d.id !== docId));
      showToast('Documento eliminado correctamente');
    } catch (e) {
      console.error('Error eliminando documento:', e);
      showToast('Error eliminando documento');
    }
  };

  // ===== EFECTOS =====
  useEffect(() => {
    // Cargar conversaciones
    listAdminConversations().then((data: any) => {
      if (Array.isArray(data)) {
        const mapped = data.map((c: any) => ({
          id: String(c.id),
          titulo: c.title,
          usuarios: c.users || [],
          archivos: (c.files || []).map((f: any) => ({ id: f.filename, name: f.filename, size: 0, type: '' })),
          fechaCreacion: new Date(c.created_at).toISOString(),
        }));
        setConvs(mapped);
      }
    }).catch(console.error);

    // Cargar chatbots
    listUserChatbots().then((data: Chatbot[]) => {
      setChatbots(data);
    }).catch(console.error);
  }, []);

  // Paginación para conversaciones
  const totalPages = Math.max(1, Math.ceil(convs.length / PAGE_SIZE));
  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);
  
  const pageItems = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
    return convs.slice(start, end);
  }, [convs, page]);

  // ===== RENDER =====
  return (
    <div className="admin-wrapper">
      {/* Pestañas */}
      <div className="admin-card">
        <div className="admin-card-header">
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            <button 
              className={`tab-button ${activeTab === 'conversaciones' ? 'active' : ''}`}
              onClick={() => setActiveTab('conversaciones')}
            >
              Gestión de Conversaciones
            </button>
            <button 
              className={`tab-button ${activeTab === 'chatbots' ? 'active' : ''}`}
              onClick={() => setActiveTab('chatbots')}
            >
              Gestión de Chatbots RAG
            </button>
          </div>
        </div>

        {/* Contenido de la pestaña activa */}
        {activeTab === 'conversaciones' && (
          <>
            <h2>Crear conversación</h2>
            <div className="create-form">
              <label className="field-label">
                <span>Título</span>
                <input 
                  className="cell-input" 
                  value={titulo} 
                  onChange={e => setTitulo(e.target.value)} 
                  placeholder="Asunto o título de la conversación" 
                />
              </label>

              <label className="field-label">
                <span>Usuarios (email)</span>
                <div className="user-typeahead">
                  <input
                    className="cell-input"
                    value={usuarioQuery}
                    onChange={e => setUsuarioQuery(e.target.value)}
                    placeholder="Escriba el email del usuario..."
                  />
                  {usuarioQuery && emailSuggestions.length > 0 && (
                    <div className="suggestions">
                      {emailSuggestions.slice(0, 5).map(s => (
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
                <span>Archivos opcionales</span>
                <input 
                  ref={fileInputRef}
                  type="file" 
                  multiple 
                  accept={acceptAttr} 
                  onChange={e => onPickArchivos(e.target.files)}
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
                <button className="small" onClick={() => { setTitulo(''); setUsuarios([]); setArchivos([]); setUsuarioQuery(''); }}>
                  Cancelar
                </button>
                <button 
                  className="small primary" 
                  onClick={crearConversacion} 
                  disabled={!isValidConv || creating}
                >
                  {creating ? 'Creando...' : 'Crear'}
                </button>
              </div>
            </div>
          </>
        )}

        {activeTab === 'chatbots' && (
          <>
            <h2>Crear Chatbot RAG</h2>
            <div className="create-form">
              <label className="field-label">
                <span>Título del Chatbot</span>
                <input 
                  className="cell-input" 
                  value={chatbotTitle} 
                  onChange={e => setChatbotTitle(e.target.value)} 
                  placeholder="Nombre del chatbot personalizado" 
                />
              </label>

              <label className="field-label">
                <span>Descripción (opcional)</span>
                <textarea 
                  className="cell-input" 
                  value={chatbotDescription} 
                  onChange={e => setChatbotDescription(e.target.value)} 
                  placeholder="Describe el propósito y alcance de este chatbot..."
                  rows={3}
                />
              </label>

              <div className="create-actions">
                <button className="small" onClick={() => { setChatbotTitle(''); setChatbotDescription(''); }}>
                  Cancelar
                </button>
                <button 
                  className="small primary" 
                  onClick={crearChatbot} 
                  disabled={!isValidChatbot || creatingChatbot}
                >
                  {creatingChatbot ? 'Creando...' : 'Crear Chatbot'}
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Lista de conversaciones */}
      {activeTab === 'conversaciones' && (
        <div className="admin-card" style={{ marginTop: 16 }}>
          <div className="admin-card-header">
            <h2>Gestión de conversaciones ({convs.length})</h2>
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
                      <button 
                        className="small" 
                        title="Eliminar" 
                        disabled={deletingId === c.id} 
                        onClick={async () => {
                          if (!confirm('¿Eliminar esta conversación?')) return;
                          setDeletingId(c.id);
                          try {
                            await deleteAdminConversation(Number(c.id));
                            setConvs(prev => prev.filter(conv => conv.id !== c.id));
                            showToast('Conversación eliminada');
                          } catch (err) {
                            console.error('Error eliminando conversación:', err);
                            showToast('Error eliminando conversación');
                          } finally {
                            setDeletingId(null);
                          }
                        }}
                      >
                        Eliminar
                      </button>
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
              <button className="small" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                Anterior
              </button>
              <span className="page-indicator">Página {page} de {totalPages}</span>
              <button className="small" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
                Siguiente
              </button>
            </div>
          )}
        </div>
      )}

      {/* Lista de chatbots */}
      {activeTab === 'chatbots' && (
        <div className="admin-card" style={{ marginTop: 16 }}>
          <div className="admin-card-header">
            <h2>Chatbots RAG ({chatbots.length})</h2>
          </div>
          
          <div style={{ display: 'flex', gap: 16 }}>
            {/* Lista de chatbots */}
            <div style={{ flex: 1 }}>
              <div className="table-scroll">
                <table className="users-table">
                  <thead>
                    <tr>
                      <th>Título</th>
                      <th>Documentos</th>
                      <th>Usuarios</th>
                      <th>Estado</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {chatbots.map(chatbot => (
                      <tr 
                        key={chatbot.id} 
                        className={`fixed-height ${selectedChatbot?.id === chatbot.id ? 'selected' : ''}`}
                        onClick={() => seleccionarChatbot(chatbot)}
                        style={{ cursor: 'pointer' }}
                      >
                        <td>
                          <div>
                            <strong>{chatbot.title}</strong>
                            {chatbot.description && <div style={{ fontSize: '0.9em', color: '#666' }}>{chatbot.description}</div>}
                          </div>
                        </td>
                        <td>{chatbot.documents_count}</td>
                        <td>{chatbot.users_count}</td>
                        <td>
                          <span className={`status ${chatbot.is_active ? 'active' : 'inactive'}`}>
                            {chatbot.is_active ? 'Activo' : 'Inactivo'}
                          </span>
                        </td>
                        <td>
                          <button 
                            className="small danger" 
                            disabled={deletingChatbot === chatbot.id}
                            onClick={(e) => {
                              e.stopPropagation();
                              eliminarChatbot(chatbot.id);
                            }}
                          >
                            {deletingChatbot === chatbot.id ? 'Eliminando...' : 'Eliminar'}
                          </button>
                        </td>
                      </tr>
                    ))}
                    {chatbots.length === 0 && (
                      <tr>
                        <td colSpan={5} style={{ textAlign: 'center', color: '#666' }}>Aún no hay chatbots</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Panel de documentos del chatbot seleccionado */}
            {selectedChatbot && (
              <div style={{ flex: 1 }}>
                <div className="admin-card-header">
                  <h3>Documentos de "{selectedChatbot.title}"</h3>
                </div>
                
                <div className="create-form">
                  <label className="field-label">
                    <span>Subir documentos para entrenar el chatbot</span>
                    <input 
                      ref={chatbotFileInputRef}
                      type="file" 
                      multiple 
                      accept={acceptAttr}
                      onChange={e => subirDocumentos(e.target.files)}
                      disabled={uploadingDocs}
                    />
                  </label>
                  
                  <div className="create-actions">
                    <button 
                      className="small primary"
                      onClick={procesarDocumentos}
                      disabled={processingDocs || chatbotDocuments.length === 0}
                    >
                      {processingDocs ? 'Procesando...' : 'Procesar Documentos'}
                    </button>
                  </div>
                </div>

                <div className="files-list" style={{ maxHeight: 400, overflowY: 'auto' }}>
                  {uploadingDocs && (
                    <div style={{ padding: 16, textAlign: 'center', color: '#666' }}>
                      Subiendo documentos...
                    </div>
                  )}
                  
                  {chatbotDocuments.length === 0 && !uploadingDocs ? (
                    <div style={{ padding: 16, textAlign: 'center', color: '#666' }}>
                      No hay documentos. Sube algunos archivos para entrenar el chatbot.
                    </div>
                  ) : (
                    chatbotDocuments.map(doc => (
                      <div key={doc.id} className="file-row">
                        <div>
                          <strong>{doc.original_filename}</strong>
                          <div style={{ fontSize: '0.8em', color: '#666' }}>
                            {Math.ceil(doc.file_size / 1024)} KB • 
                            {doc.is_processed ? ` ${doc.chunks_count} chunks procesados` : ' Pendiente de procesar'}
                          </div>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span 
                            className={`status ${doc.is_processed ? 'processed' : 'pending'}`}
                            style={{ fontSize: '0.8em' }}
                          >
                            {doc.is_processed ? '✓ Procesado' : '⏳ Pendiente'}
                          </span>
                          <button 
                            className="small danger" 
                            onClick={() => eliminarDocumento(doc.id)}
                          >
                            Eliminar
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Toast Container */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast ${toast.show ? 'toast-visible' : ''}`}>
            {toast.message}
          </div>
        ))}
      </div>

      {/* Modales */}
      {viewConv && (
        <div className="report-modal-overlay" onClick={() => setViewConv(null)}>
          <div className="report-modal-content" onClick={e => e.stopPropagation()}>
            <div className="report-modal-header">
              <h3>Detalle de conversación</h3>
              <button className="close-button" onClick={() => setViewConv(null)}>×</button>
            </div>
            <div className="report-modal-body">
              <div className="form-group">
                <label>Título:</label>
                <div className="detail-text">{viewConv.titulo}</div>
              </div>
              <div className="form-group">
                <label>Usuarios:</label>
                <div className="detail-text">{viewConv.usuarios.join(', ')}</div>
              </div>
              <div className="form-group">
                <label>Archivos:</label>
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
              <div className="form-group">
                <label>Fecha de creación:</label>
                <div className="detail-text">{new Date(viewConv.fechaCreacion).toLocaleString()}</div>
              </div>
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

// ===== MODAL PARA EDITAR ARCHIVOS =====
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
    if (fileInputRef.current && fileInputRef.current.files && fileInputRef.current.files.length > 0) {
      setUploading(true);
      try {
        const form = new FormData();
        for (const f of Array.from(fileInputRef.current.files)) form.append('files', f as File);
        await uploadConversationAttachments(Number(conv.id), form);
        
        // Recargar conversaciones para obtener la lista actualizada
        const latest: any = await listAdminConversations();
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
          <button className="submit-button" disabled={uploading} onClick={doSave}>
            {uploading ? 'Subiendo...' : 'Guardar'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateConversation;