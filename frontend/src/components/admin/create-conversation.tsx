import React, { useState, useEffect, useRef } from 'react';
import './create-conversation.css';

// Importamos las APIs de chatbots pero las usamos como APIs de conversaciones
import { 
  createChatbot as createConversation,
  listUserChatbots as listConversations, 
  deleteChatbot as deleteConversacion,
  uploadDocuments as uploadConversationDocuments,
  processDocuments as processConversationDocuments,
  listChatbotDocuments as listConversationDocuments,
  deleteChatbotDocument as deleteConversationDocument,
  listChatbotUsers,
  grantUserAccess,
  revokeChatbotAccess,
  fetchUsers
} from '../../lib/api';

// Tipos adaptados para conversaciones
interface Conversation {
  id: number;
  name: string;
  description?: string;
  documentCount?: number;
  created_at?: string;
  is_active?: boolean;
}

interface ConversationFile {
  id: string;
  name: string;
  size: number;
  type: string;
}

interface ConversationDocument {
  id: string;
  original_filename: string;
  file_size: number;
  is_processed: boolean;
  chunks_count?: number;
}

interface ConversationUser {
  id: number;
  user_id: number;
  user_email: string;
  user_name?: string;
  access_level: 'READ' | 'WRITE' | 'ADMIN';
  granted_at: string;
}

interface SystemUser {
  id: number;
  email: string;
  nombre?: string;
  activo: boolean;
}

const acceptMime = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'text/plain',
  'text/csv'
];

const acceptAttr = '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv';

const CreateConversation: React.FC = () => {
  // Estados para conversaciones
  const [conversaciones, setConversaciones] = useState<Conversation[]>([]);
  const [titulo, setTitulo] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [usuarios, setUsuarios] = useState<string[]>([]);
  const [usuarioQuery, setUsuarioQuery] = useState('');
  const [archivos, setArchivos] = useState<ConversationFile[]>([]);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Estados para usuarios
  const [allUsers, setAllUsers] = useState<SystemUser[]>([]);

  // Estados para documentos
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [conversationDocuments, setConversationDocuments] = useState<ConversationDocument[]>([]);
  const [uploadingDocs, setUploadingDocs] = useState(false);
  const [processingDocs, setProcessingDocs] = useState(false);

  // Estados para gestión de usuarios
  const [conversationUsers, setConversationUsers] = useState<ConversationUser[]>([]);
  const [showUserModal, setShowUserModal] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserAccessLevel, setNewUserAccessLevel] = useState<'read' | 'write' | 'admin'>('read');
  const [managingUsers, setManagingUsers] = useState(false);

  // Referencias
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const conversationFileInputRef = useRef<HTMLInputElement | null>(null);

  // Estados para toast
  const [toasts, setToasts] = useState<Array<{id: string, message: string, show: boolean}>>([]);

  // Sugerencias de email para buscar usuarios
  const emailSuggestions = allUsers.filter(user => 
    user.email.toLowerCase().includes(usuarioQuery.toLowerCase()) && user.activo
  );

  // Sugerencias de email para agregar usuarios
  const userEmailSuggestions = allUsers.filter(user => 
    user.email.toLowerCase().includes(newUserEmail.toLowerCase()) && user.activo
  );

  // Validaciones
  const isValidConv = titulo.trim().length > 0;

  // Toast functions
  const showToast = (message: string) => {
    const id = Date.now().toString();
    const newToast = { id, message, show: false };
    setToasts(prev => [...prev, newToast]);
    
    setTimeout(() => {
      setToasts(prev => prev.map(t => t.id === id ? { ...t, show: true } : t));
    }, 100);
    
    setTimeout(() => {
      setToasts(prev => prev.map(t => t.id === id ? { ...t, show: false } : t));
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, 300);
    }, 3000);
  };

  // Cargar conversaciones y usuarios al inicio
  useEffect(() => {
    cargarConversaciones();
    cargarUsuarios();
  }, []);

  const cargarUsuarios = async () => {
    try {
      const usuarios = await fetchUsers();
      setAllUsers(usuarios);
    } catch (error) {
      console.error('Error al cargar usuarios:', error);
      setAllUsers([]);
    }
  };

  const cargarConversaciones = async () => {
    try {
      const data = await listConversations();
      if (Array.isArray(data)) {
        const mappedConversations: Conversation[] = data.map(chatbot => ({
          id: chatbot.id,
          name: chatbot.title || chatbot.name,
          description: chatbot.description,
          documentCount: chatbot.documents_count,
          created_at: chatbot.created_at,
          is_active: chatbot.is_active
        }));
        setConversaciones(mappedConversations);
      }
    } catch (error) {
      console.error('Error cargando conversaciones:', error);
      showToast('Error cargando conversaciones');
    }
  };

  const crearConversacion = async () => {
    if (!isValidConv) return;
    
    setCreating(true);
    try {
      // Crear conversación usando la API de chatbots internamente
      const newConversation = await createConversation({
        title: titulo,
        description: descripcion
      });

      console.log('Conversación creada:', newConversation);

      // Si hay archivos, subirlos
      if (fileInputRef.current?.files && fileInputRef.current.files.length > 0) {
        console.log('Subiendo archivos:', fileInputRef.current.files);
        
        try {
          const uploadResult = await uploadConversationDocuments(newConversation.id, fileInputRef.current.files);
          console.log('Archivos subidos:', uploadResult);
          
          // Procesar documentos
          await processConversationDocuments(newConversation.id);
          console.log('Documentos procesados');
        } catch (uploadError) {
          console.error('Error subiendo/procesando archivos:', uploadError);
          // No fallar la creación por error de archivos
          showToast('Conversación creada, pero hubo error subiendo archivos');
        }
      }

      // Limpiar formulario
      setTitulo('');
      setDescripcion('');
      setUsuarios([]);
      setArchivos([]);
      setUsuarioQuery('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      // Recargar lista
      await cargarConversaciones();
      showToast('Conversación creada exitosamente');
    } catch (error) {
      console.error('Error creando conversación:', error);
      showToast('Error creando conversación');
    } finally {
      setCreating(false);
    }
  };

  const eliminarConversacion = async (id: number) => {
    if (!confirm('¿Eliminar esta conversación?')) return;
    
    setDeleting(true);
    try {
      await deleteConversacion(id);
      setConversaciones(prev => prev.filter(conv => conv.id !== id));
      if (selectedConversation?.id === id) {
        setSelectedConversation(null);
      }
      showToast('Conversación eliminada');
    } catch (error) {
      console.error('Error eliminando conversación:', error);
      showToast('Error eliminando conversación');
    } finally {
      setDeleting(false);
    }
  };

  const addUsuario = (email: string) => {
    if (email && !usuarios.includes(email)) {
      setUsuarios(prev => [...prev, email]);
      setUsuarioQuery('');
    }
  };

  const removeUsuario = (email: string) => {
    setUsuarios(prev => prev.filter(u => u !== email));
  };

  const onPickArchivos = (files: FileList | null) => {
    if (!files) return;
    
    const newFiles: ConversationFile[] = [];
    for (const file of Array.from(files)) {
      if (acceptMime.includes(file.type) || acceptAttr.split(',').some(ext => file.name.toLowerCase().endsWith(ext.trim()))) {
        newFiles.push({
          id: crypto.randomUUID(),
          name: file.name,
          size: file.size,
          type: file.type
        });
      }
    }
    setArchivos(prev => [...prev, ...newFiles]);
    console.log('Archivos seleccionados:', newFiles); // Debug
  };

  const removeArchivo = (id: string) => {
    setArchivos(prev => prev.filter(a => a.id !== id));
  };

  const seleccionarConversacion = async (conversation: Conversation) => {
    setSelectedConversation(conversation);
    
    try {
      // Cargar documentos
      const docs = await listConversationDocuments(conversation.id);
      setConversationDocuments(docs || []);
      
      // Cargar usuarios con acceso
      const users = await listChatbotUsers(conversation.id);
      setConversationUsers(users || []);
    } catch (error) {
      console.error('Error cargando datos de conversación:', error);
      showToast('Error cargando detalles de la conversación');
    }
  };

  const agregarUsuario = async () => {
    if (!selectedConversation || !newUserEmail.trim()) return;
    
    setManagingUsers(true);
    try {
      // Buscar el usuario por email en la lista de usuarios disponibles
      const userToAdd = allUsers.find(user => user.email === newUserEmail.trim());
      if (!userToAdd) {
        showToast('Usuario no encontrado');
        return;
      }
      
      await grantUserAccess(selectedConversation.id, {
        user_ids: [userToAdd.id],
        access_level: newUserAccessLevel
      });
      
      // Recargar lista de usuarios
      const updatedUsers = await listChatbotUsers(selectedConversation.id);
      setConversationUsers(updatedUsers || []);
      
      setNewUserEmail('');
      setNewUserAccessLevel('read');
      showToast('Usuario agregado exitosamente');
    } catch (error) {
      console.error('Error agregando usuario:', error);
      showToast('Error agregando usuario');
    } finally {
      setManagingUsers(false);
    }
  };

  const removerUsuario = async (userId: number) => {
    if (!selectedConversation) return;
    
    if (!confirm('¿Eliminar acceso de este usuario?')) return;
    
    setManagingUsers(true);
    try {
      await revokeChatbotAccess(selectedConversation.id, userId);
      
      // Recargar lista de usuarios
      const updatedUsers = await listChatbotUsers(selectedConversation.id);
      setConversationUsers(updatedUsers || []);
      
      showToast('Acceso revocado exitosamente');
    } catch (error) {
      console.error('Error removiendo usuario:', error);
      showToast('Error removiendo acceso');
    } finally {
      setManagingUsers(false);
    }
  };

  const subirDocumentos = async (files: FileList | null) => {
    if (!files || !selectedConversation) return;
    
    setUploadingDocs(true);
    try {
      await uploadConversationDocuments(selectedConversation.id, files);
      
      // Recargar documentos
      const docs = await listConversationDocuments(selectedConversation.id);
      setConversationDocuments(docs || []);
      
      showToast('Documentos subidos exitosamente');
    } catch (error) {
      console.error('Error subiendo documentos:', error);
      showToast('Error subiendo documentos');
    } finally {
      setUploadingDocs(false);
    }
  };

  const procesarDocumentos = async () => {
    if (!selectedConversation) return;
    
    setProcessingDocs(true);
    try {
      await processConversationDocuments(selectedConversation.id);
      
      // Recargar documentos después de un delay para permitir el procesamiento
      setTimeout(async () => {
        const docs = await listConversationDocuments(selectedConversation.id);
        setConversationDocuments(docs || []);
      }, 2000);
      
      showToast('Procesamiento iniciado. Los documentos se actualizarán en breve.');
    } catch (error) {
      console.error('Error procesando documentos:', error);
      showToast('Error procesando documentos');
    } finally {
      setProcessingDocs(false);
    }
  };

  const eliminarDocumento = async (documentId: number) => {
    if (!selectedConversation) return;
    
    if (!confirm('¿Eliminar este documento?')) return;
    
    try {
      await deleteConversationDocument(selectedConversation.id, documentId);
      
      // Recargar documentos
      const docs = await listConversationDocuments(selectedConversation.id);
      setConversationDocuments(docs || []);
      
      showToast('Documento eliminado exitosamente');
    } catch (error) {
      console.error('Error eliminando documento:', error);
      showToast('Error eliminando documento');
    }
  };

  return (
    <div className="admin-wrapper">
      {/* Gestión de Conversaciones (usando lógica RAG internamente) */}
      <div className="admin-card">
        <div className="admin-card-header">
          <h2>Crear conversación</h2>
        </div>
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
            <span>Descripción (opcional)</span>
            <textarea 
              className="cell-input" 
              value={descripcion} 
              onChange={e => setDescripcion(e.target.value)} 
              placeholder="Describe el propósito y alcance de esta conversación..."
              rows={3}
            />
          </label>

          <label className="field-label">
            <span>Usuarios (email) - Opcional</span>
            <div className="user-typeahead">
              <input
                className="cell-input"
                value={usuarioQuery}
                onChange={e => setUsuarioQuery(e.target.value)}
                placeholder="Escriba el email del usuario..."
              />
              {usuarioQuery && emailSuggestions.length > 0 && (
                <div className="suggestions">
                  {emailSuggestions.slice(0, 5).map(user => (
                    <div key={user.email} className="suggestion-item" onClick={() => addUsuario(user.email)}>
                      {user.email} - {user.nombre}
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

          {/* Gestión de documentos */}
          <div className="documents-section">
            <h3>Documentos de la conversación</h3>
            <label className="field-label">
              <span>Agregar archivos</span>
              <input 
                ref={fileInputRef}
                type="file" 
                multiple 
                accept={acceptAttr} 
                onChange={e => onPickArchivos(e.target.files)}
              />
            </label>
            
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
          </div>

          <div className="create-actions">
            <button className="small" onClick={() => { 
              setTitulo(''); 
              setDescripcion(''); 
              setUsuarios([]); 
              setArchivos([]); 
              setUsuarioQuery(''); 
            }}>
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
      </div>

      {/* Lista de conversaciones existentes - Versión mejorada */}
      {conversaciones.length > 0 && (
        <div className="admin-card" style={{ marginTop: 16 }}>
          <div className="admin-card-header">
            <h2>Conversaciones existentes ({conversaciones.length})</h2>
          </div>
          <div style={{ display: 'flex', gap: 16, minHeight: 400 }}>
            {/* Lista de conversaciones */}
            <div style={{ flex: 1, borderRight: '1px solid #e0e0e0', paddingRight: 16 }}>
              <div className="conversations-grid" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {conversaciones.map(conv => (
                  <div 
                    key={conv.id} 
                    className={`conversation-card ${selectedConversation?.id === conv.id ? 'selected' : ''}`}
                    onClick={() => seleccionarConversacion(conv)}
                    style={{ 
                      cursor: 'pointer',
                      padding: 16,
                      border: '1px solid #e0e0e0',
                      borderRadius: 8,
                      backgroundColor: selectedConversation?.id === conv.id ? '#f0f8ff' : 'white',
                      borderColor: selectedConversation?.id === conv.id ? '#007acc' : '#e0e0e0',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                      <h3 style={{ margin: 0, fontSize: '1.1em', color: '#333' }}>{conv.name}</h3>
                      <button 
                        className="small delete-btn" 
                        onClick={(e) => {
                          e.stopPropagation();
                          eliminarConversacion(conv.id);
                        }}
                        disabled={deleting}
                        style={{
                          background: '#ff4757',
                          color: 'white',
                          border: 'none',
                          borderRadius: 4,
                          padding: '4px 8px',
                          fontSize: '0.8em',
                          cursor: 'pointer'
                        }}
                      >
                        {deleting ? 'Eliminando...' : '🗑️'}
                      </button>
                    </div>
                    
                    {conv.description && (
                      <p style={{ margin: '8px 0', color: '#666', fontSize: '0.9em', lineHeight: 1.4 }}>
                        {conv.description}
                      </p>
                    )}
                    
                    <div style={{ display: 'flex', gap: 16, marginTop: 12 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <span style={{ fontSize: '1.1em' }}>📄</span>
                        <small style={{ color: '#666' }}>
                          {conv.documentCount || 0} documentos
                        </small>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <span style={{ fontSize: '1.1em' }}>👥</span>
                        <small style={{ color: '#666' }}>
                          {selectedConversation?.id === conv.id ? conversationUsers.length : '?'} usuarios
                        </small>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <span style={{ 
                          fontSize: '0.8em', 
                          padding: '2px 6px', 
                          borderRadius: 12,
                          backgroundColor: conv.is_active ? '#27ae60' : '#95a5a6',
                          color: 'white'
                        }}>
                          {conv.is_active ? 'Activa' : 'Inactiva'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
                
                {conversaciones.length === 0 && (
                  <div style={{ textAlign: 'center', color: '#666', padding: 40 }}>
                    <div style={{ fontSize: '3em', marginBottom: 16 }}>💬</div>
                    <p>No hay conversaciones creadas aún</p>
                    <p style={{ fontSize: '0.9em' }}>Crea tu primera conversación usando el formulario de arriba</p>
                  </div>
                )}
              </div>
            </div>

            {/* Panel de detalles de la conversación seleccionada */}
            {selectedConversation ? (
              <div style={{ flex: 1, paddingLeft: 16 }}>
                <div style={{ marginBottom: 24 }}>
                  <h3 style={{ margin: '0 0 16px 0', color: '#333', borderBottom: '1px solid #e0e0e0', paddingBottom: 8 }}>
                    📋 Detalles de "{selectedConversation.name}"
                  </h3>
                  
                  {/* Gestión de usuarios */}
                  <div style={{ marginBottom: 24 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                      <h4 style={{ margin: 0, color: '#555' }}>👥 Usuarios con acceso</h4>
                      <button 
                        className="small primary"
                        onClick={() => setShowUserModal(!showUserModal)}
                        style={{ fontSize: '0.8em' }}
                      >
                        + Agregar Usuario
                      </button>
                    </div>
                    
                    {/* Formulario para agregar usuario */}
                    {showUserModal && (
                      <div style={{ 
                        background: '#f8f9fa', 
                        border: '1px solid #e0e0e0', 
                        borderRadius: 6, 
                        padding: 12, 
                        marginBottom: 12 
                      }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
                          <div style={{ flex: 1, position: 'relative' }}>
                            <label style={{ display: 'block', fontSize: '0.8em', marginBottom: 4, color: '#666' }}>
                              Email del usuario
                            </label>
                            <input
                              type="email"
                              className="cell-input"
                              value={newUserEmail}
                              onChange={e => setNewUserEmail(e.target.value)}
                              placeholder="usuario@empresa.com"
                              style={{ fontSize: '0.9em', padding: '6px 8px' }}
                            />
                            {newUserEmail && userEmailSuggestions.length > 0 && (
                              <div className="suggestions" style={{ 
                                position: 'absolute', 
                                top: '100%', 
                                left: 0, 
                                right: 0, 
                                zIndex: 1000,
                                backgroundColor: 'white',
                                border: '1px solid #ddd',
                                borderRadius: 4,
                                maxHeight: 150,
                                overflowY: 'auto',
                                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                              }}>
                                {userEmailSuggestions.slice(0, 5).map(user => (
                                  <div 
                                    key={user.email} 
                                    className="suggestion-item" 
                                    onClick={() => setNewUserEmail(user.email)}
                                    style={{
                                      padding: '6px 8px',
                                      cursor: 'pointer',
                                      fontSize: '0.85em',
                                      borderBottom: '1px solid #eee'
                                    }}
                                    onMouseEnter={e => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                                    onMouseLeave={e => e.currentTarget.style.backgroundColor = 'white'}
                                  >
                                    <strong>{user.email}</strong> - {user.nombre}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                          <div>
                            <label style={{ display: 'block', fontSize: '0.8em', marginBottom: 4, color: '#666' }}>
                              Nivel de acceso
                            </label>
                            <select
                              className="cell-input"
                              value={newUserAccessLevel}
                              onChange={e => setNewUserAccessLevel(e.target.value as any)}
                              style={{ fontSize: '0.9em', padding: '6px 8px' }}
                            >
                              <option value="read">Solo lectura</option>
                              <option value="write">Lectura y escritura</option>
                              <option value="admin">Administrador</option>
                            </select>
                          </div>
                          <button 
                            className="small primary"
                            onClick={agregarUsuario}
                            disabled={managingUsers || !newUserEmail.trim()}
                            style={{ fontSize: '0.8em' }}
                          >
                            {managingUsers ? 'Agregando...' : 'Agregar'}
                          </button>
                        </div>
                      </div>
                    )}
                    
                    {/* Lista de usuarios */}
                    <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                      {conversationUsers.length === 0 ? (
                        <div style={{ textAlign: 'center', color: '#666', padding: 20, fontSize: '0.9em' }}>
                          No hay usuarios con acceso aún
                        </div>
                      ) : (
                        conversationUsers.map(user => (
                          <div 
                            key={user.id} 
                            style={{ 
                              display: 'flex', 
                              justifyContent: 'space-between', 
                              alignItems: 'center',
                              padding: '8px 12px',
                              border: '1px solid #e8e8e8',
                              borderRadius: 4,
                              marginBottom: 6,
                              backgroundColor: 'white'
                            }}
                          >
                            <div>
                              <div style={{ fontWeight: 500, fontSize: '0.9em' }}>
                                {user.user_email}
                              </div>
                              <div style={{ fontSize: '0.8em', color: '#666' }}>
                                {user.user_name && `${user.user_name} • `}
                                <span style={{
                                  padding: '1px 6px',
                                  borderRadius: 8,
                                  fontSize: '0.7em',
                                  backgroundColor: user.access_level === 'ADMIN' ? '#e74c3c' : 
                                                 user.access_level === 'WRITE' ? '#f39c12' : '#3498db',
                                  color: 'white'
                                }}>
                                  {user.access_level}
                                </span>
                              </div>
                            </div>
                            <button 
                              className="small"
                              onClick={() => removerUsuario(user.user_id)}
                              disabled={managingUsers}
                              style={{ 
                                background: '#e74c3c', 
                                color: 'white', 
                                border: 'none',
                                fontSize: '0.7em',
                                padding: '3px 6px'
                              }}
                            >
                              Remover
                            </button>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                  
                  {/* Gestión de documentos */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                      <h4 style={{ margin: 0, color: '#555' }}>📄 Documentos</h4>
                      <input 
                        ref={conversationFileInputRef}
                        type="file" 
                        multiple 
                        accept={acceptAttr}
                        onChange={e => subirDocumentos(e.target.files)}
                        disabled={uploadingDocs}
                        style={{ fontSize: '0.8em' }}
                      />
                    </div>
                    
                    <div style={{ maxHeight: 300, overflowY: 'auto' }}>
                      {uploadingDocs && (
                        <div style={{ textAlign: 'center', padding: 20, color: '#666', fontSize: '0.9em' }}>
                          📤 Subiendo documentos...
                        </div>
                      )}
                      
                      {conversationDocuments.length === 0 && !uploadingDocs ? (
                        <div style={{ textAlign: 'center', color: '#666', padding: 20, fontSize: '0.9em' }}>
                          <div style={{ fontSize: '2em', marginBottom: 8 }}>📁</div>
                          <p>No hay documentos subidos</p>
                          <p style={{ fontSize: '0.8em' }}>Sube algunos archivos para entrenar la conversación</p>
                        </div>
                      ) : (
                        conversationDocuments.map(doc => (
                          <div 
                            key={doc.id} 
                            style={{ 
                              display: 'flex', 
                              justifyContent: 'space-between', 
                              alignItems: 'center',
                              padding: '10px 12px',
                              border: '1px solid #e8e8e8',
                              borderRadius: 4,
                              marginBottom: 8,
                              backgroundColor: 'white'
                            }}
                          >
                            <div style={{ flex: 1 }}>
                              <div style={{ fontWeight: 500, fontSize: '0.9em' }}>
                                {doc.original_filename}
                              </div>
                              <div style={{ fontSize: '0.8em', color: '#666', marginTop: 2 }}>
                                {Math.ceil(doc.file_size / 1024)} KB • 
                                {doc.is_processed ? 
                                  ` ✅ ${doc.chunks_count || 0} chunks procesados` : 
                                  ' ⏳ Pendiente de procesar'
                                }
                              </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                              <span 
                                style={{ 
                                  fontSize: '0.7em',
                                  padding: '2px 6px',
                                  borderRadius: 8,
                                  backgroundColor: doc.is_processed ? '#27ae60' : '#f39c12',
                                  color: 'white'
                                }}
                              >
                                {doc.is_processed ? 'Procesado' : 'Pendiente'}
                              </span>
                              <button 
                                className="small" 
                                onClick={() => eliminarDocumento(Number(doc.id))}
                                style={{ 
                                  background: '#e74c3c', 
                                  color: 'white', 
                                  border: 'none',
                                  fontSize: '0.7em',
                                  padding: '3px 6px'
                                }}
                              >
                                🗑️
                              </button>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                    
                    {conversationDocuments.some(doc => !doc.is_processed) && (
                      <div style={{ marginTop: 12, textAlign: 'center' }}>
                        <button 
                          className="small primary"
                          onClick={procesarDocumentos}
                          disabled={processingDocs}
                          style={{ fontSize: '0.8em' }}
                        >
                          {processingDocs ? '⚙️ Procesando...' : '⚙️ Procesar Documentos Pendientes'}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ 
                flex: 1, 
                paddingLeft: 16, 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                color: '#666',
                textAlign: 'center'
              }}>
                <div>
                  <div style={{ fontSize: '3em', marginBottom: 16 }}>👈</div>
                  <p>Selecciona una conversación</p>
                  <p style={{ fontSize: '0.9em' }}>para ver sus detalles y gestionar usuarios</p>
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
    </div>
  );
};

export default CreateConversation;