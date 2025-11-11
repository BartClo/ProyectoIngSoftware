import React, { useEffect, useMemo, useState } from 'react';
import './users-table.css';
import { useAdminData } from './admin-data-context';
import { createAdminUser, updateUserPassword } from '../../lib/api';

type Role = 'admin' | 'docente';

export interface UserRow {
  id: string;
  nombre: string;
  email: string;
  rol: Role;
  activo: boolean;
}

interface PasswordChangeState {
  userId: string;
  password: string;
  confirmPassword: string;
  showPassword: boolean;
  validationErrors: string[];
}

const UsersTable: React.FC = () => {
  const { users: usersCtx, setUsers: setUsersCtx, refreshUsers } = useAdminData();
  const [users, setUsers] = useState<UserRow[]>(usersCtx);
  
  // Mantener el estado local sincronizado con el contexto
  React.useEffect(() => {
    setUsers(usersCtx);
  }, [usersCtx]);
  
  const [query, setQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<Partial<UserRow> & { password?: string }>({});
  const [newRowId, setNewRowId] = useState<string | null>(null);
  
  // Estado para gestión de contraseñas (Nielsen H2: Visibilidad del estado del sistema)
  const [passwordMode, setPasswordMode] = useState<string | null>(null);
  const [passwordData, setPasswordData] = useState<PasswordChangeState>({
    userId: '',
    password: '',
    confirmPassword: '',
    showPassword: false,
    validationErrors: []
  });

  // Validación de contraseña en tiempo real (Nielsen H5: Prevención de errores)
  const validatePassword = (pwd: string, confirmPwd: string): string[] => {
    const errors: string[] = [];
    
    if (pwd.length < 8) {
      errors.push('Mínimo 8 caracteres');
    }
    if (!/[A-Z]/.test(pwd)) {
      errors.push('Requiere mayúscula');
    }
    if (!/[a-z]/.test(pwd)) {
      errors.push('Requiere minúscula');
    }
    if (!/[0-9]/.test(pwd)) {
      errors.push('Requiere número');
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) {
      errors.push('Requiere carácter especial');
    }
    if (confirmPwd && pwd !== confirmPwd) {
      errors.push('Las contraseñas no coinciden');
    }
    
    return errors;
  };

  // Nielsen H1: Calculadora de fortaleza de contraseña (Visibilidad del estado del sistema)
  const getPasswordStrength = (pwd: string): { level: 'weak' | 'medium' | 'strong', label: string } => {
    let score = 0;
    
    if (pwd.length >= 8) score++;
    if (pwd.length >= 12) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[a-z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) score++;
    
    if (score >= 5) return { level: 'strong', label: 'Fuerte' };
    if (score >= 3) return { level: 'medium', label: 'Media' };
    return { level: 'weak', label: 'Débil' };
  };

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return users;
    return users.filter(u =>
      u.nombre.toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q) ||
      u.rol.toLowerCase().includes(q)
    );
  }, [users, query]);

  // Paginación para evitar scroll
  const PAGE_SIZE = 8;
  const [page, setPage] = useState(1);
  useEffect(() => { setPage(1); }, [query]);
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);
  const pageItems = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
    return filtered.slice(start, end);
  }, [filtered, page]);

  const startEdit = (id: string) => {
    const u = users.find(x => x.id === id);
    if (!u) return;
    setEditingId(id);
    setDraft({ ...u });
  };

  const cancelEdit = (reason: 'cancel' | 'save' = 'cancel') => {
    // Si se estaba creando un usuario nuevo y el motivo es cancelar, eliminar la fila
    if (reason === 'cancel' && newRowId && editingId === newRowId) {
      setUsers(prev => prev.filter(u => u.id !== newRowId));
      setNewRowId(null);
      showToast('Creación cancelada');
    }
    setEditingId(null);
    setDraft({});
  };

  const saveEdit = () => {
    if (!editingId) return;
    const isNew = newRowId && editingId === newRowId;
    
    // Si es nuevo, llamar a backend
    if (isNew) {
      const payload = { 
        email: draft.email as string, 
        password: (draft.password || 'ChangeMe123!'), 
        nombre: draft.nombre as string 
      };
      
      // Validar contraseña antes de enviar
      const errors = validatePassword(payload.password, payload.password);
      if (errors.length > 0) {
        alert('Contraseña no cumple requisitos de seguridad:\n' + errors.join('\n'));
        return;
      }
      
      createAdminUser(payload).then(() => {
        refreshUsers().then(() => {
          showToast('Usuario creado exitosamente');
          setNewRowId(null);
          cancelEdit('save');
        });
      }).catch((e) => {
        console.error('create user', e);
        alert('Error creando usuario: ' + (e.body?.detail || 'Error desconocido'));
      });
      return;
    }
    
    const updated = users.map(u => (u.id === editingId ? { ...(u as UserRow), ...(draft as UserRow), id: u.id } : u));
    setUsers(updated);
    setUsersCtx(updated);
    showToast('Usuario actualizado correctamente');
    cancelEdit('save');
  };

  // Nueva función para cambiar contraseña (Nielsen H3: Control y libertad del usuario)
  const initiatePasswordChange = (userId: string) => {
    setPasswordMode(userId);
    setPasswordData({
      userId,
      password: '',
      confirmPassword: '',
      showPassword: false,
      validationErrors: []
    });
  };

  const cancelPasswordChange = () => {
    setPasswordMode(null);
    setPasswordData({
      userId: '',
      password: '',
      confirmPassword: '',
      showPassword: false,
      validationErrors: []
    });
  };

  const savePasswordChange = async () => {
    const { userId, password, confirmPassword } = passwordData;
    
    // Validar
    const errors = validatePassword(password, confirmPassword);
    if (errors.length > 0) {
      setPasswordData(prev => ({ ...prev, validationErrors: errors }));
      return;
    }
    
    try {
      const numericId = Number(userId);
      if (Number.isNaN(numericId)) {
        alert('Error: ID de usuario inválido');
        return;
      }
      
      await updateUserPassword(numericId, password);
      showToast('Contraseña actualizada de forma segura');
      cancelPasswordChange();
    } catch (e: any) {
      console.error('update password', e);
      alert('Error actualizando contraseña: ' + (e.body?.detail || 'Error desconocido'));
    }
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

  const removeUser = (id: string) => {
    try {
      // eslint-disable-next-line no-alert
      if (!(window as any).confirm || !(window as any).confirm('¿Eliminar usuario?')) return;
    } catch {}
    // Si la fila corresponde a un usuario real (id numérico), pedir al backend que lo elimine
    const isUuid = typeof id === 'string' && id.startsWith('u_') === false && id.length < 30;
    if (isUuid) {
      // intentar parsear como número
      const parsed = Number(id);
      if (!Number.isNaN(parsed)) {
        // Llamar al backend
        import('../../lib/api').then(mod => {
          mod.deleteAdminUser(parsed).then(() => {
            const updated = users.filter(u => u.id !== id);
            setUsers(updated);
            setUsersCtx(updated);
            showToast('Usuario eliminado');
          }).catch((e) => {
            console.error('delete user', e);
            alert('Error eliminando usuario en el servidor');
          });
        }).catch(() => {
          showToast('No fue posible eliminar en servidor');
        });
        return;
      }
    }
    // Fallback: eliminar localmente
    const updated = users.filter(u => u.id !== id);
    setUsers(updated);
    setUsersCtx(updated);
    showToast('Usuario eliminado (local)');
  };

  const addUser = () => {
    const id = crypto.randomUUID ? crypto.randomUUID() : `u_${Date.now()}`;
    const nuevo: UserRow = {
      id,
      nombre: 'Nuevo Usuario',
      email: 'nuevo@docente.uss.cl',
      rol: 'docente',
      activo: true,
    };
    const updated = [nuevo, ...users];
    setUsers(updated);
    setUsersCtx(updated);
    setEditingId(id);
    setDraft({ ...nuevo, password: '' });
    setNewRowId(id);
    setPage(1);
  };

  return (
    <div className="admin-wrapper">
      <div className="admin-card">
        <div className="admin-card-header">
          <h2>Administración de Usuarios</h2>
          <div className="actions">
            <input
              className="search"
              placeholder="Buscar por nombre, correo o rol."
              value={query}
              onChange={e => setQuery(e.target.value)}
              aria-label="Campo de búsqueda de usuarios"
            />
            <button 
              className="primary" 
              onClick={addUser}
              aria-label="Crear nuevo usuario"
            >
              Nuevo Usuario
            </button>
          </div>
        </div>

        <div className="table-scroll">
          <table className="users-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Correo</th>
                <th>Rol</th>
                <th>Contraseña</th>
                <th style={{ width: 180 }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {pageItems.map(u => (
                <tr key={u.id} className={!u.activo ? 'inactive fixed-height' : 'fixed-height'}>
                  <td>
                    {editingId === u.id ? (
                      <input
                        className="cell-input"
                        value={String(draft.nombre ?? '')}
                        onChange={e => setDraft(d => ({ ...d, nombre: e.target.value }))}
                        aria-label="Nombre del usuario"
                      />
                    ) : (
                      u.nombre
                    )}
                  </td>
                  <td>
                    {editingId === u.id ? (
                      <input
                        className="cell-input"
                        type="email"
                        value={String(draft.email ?? '')}
                        onChange={e => setDraft(d => ({ ...d, email: e.target.value }))}
                        aria-label="Correo electrónico del usuario"
                      />
                    ) : (
                      u.email
                    )}
                  </td>
                  <td>
                    {editingId === u.id ? (
                      <select
                        className="cell-input"
                        value={String(draft.rol ?? 'docente')}
                        onChange={e => setDraft(d => ({ ...d, rol: e.target.value as Role }))}
                        aria-label="Rol del usuario"
                      >
                        <option value="admin">Administrador</option>
                        <option value="docente">Docente</option>
                      </select>
                    ) : (
                      u.rol.charAt(0).toUpperCase() + u.rol.slice(1)
                    )}
                  </td>
                  <td>
                    {editingId === u.id && newRowId === u.id ? (
                      // Usuario nuevo: input de contraseña con validación completa (Nielsen H1 & H5)
                      <div className="password-change-container">
                        <div className="password-inputs">
                          <div className="password-field-wrapper">
                            <input
                              className={`cell-input ${
                                draft.password && (draft.password as string).length > 0
                                  ? (passwordData.validationErrors.length === 0 ? 'valid' : 'invalid')
                                  : ''
                              }`}
                              type={passwordData.showPassword ? 'text' : 'password'}
                              placeholder="Contraseña inicial (min. 8 caracteres)"
                              value={String(draft.password ?? '')}
                              onChange={e => {
                                const pwd = e.target.value;
                                setDraft(d => ({ ...d, password: pwd }));
                                const errors = validatePassword(pwd, pwd);
                                setPasswordData(prev => ({ ...prev, validationErrors: errors, password: pwd, confirmPassword: pwd }));
                              }}
                              aria-label="Contraseña del nuevo usuario"
                              aria-describedby="new-password-strength"
                            />
                          </div>
                          <button
                            className="toggle-visibility-btn"
                            onClick={() => setPasswordData(prev => ({ ...prev, showPassword: !prev.showPassword }))}
                            aria-label={passwordData.showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                            type="button"
                          >
                            {passwordData.showPassword ? 'Ocultar' : 'Mostrar'}
                          </button>
                        </div>
                        
                        {/* Nielsen H1: Indicador de fortaleza para nuevo usuario */}
                        {draft.password && (draft.password as string).length > 0 && (
                          <div className="password-strength-indicator" id="new-password-strength" role="status" aria-live="polite">
                            <div className="strength-bar">
                              <div className={`strength-fill ${getPasswordStrength(draft.password as string).level}`}></div>
                            </div>
                            <span className={`strength-label ${getPasswordStrength(draft.password as string).level}`}>
                              {getPasswordStrength(draft.password as string).label}
                            </span>
                          </div>
                        )}
                        
                        {/* Nielsen H9: Errores de validación descriptivos */}
                        {passwordData.validationErrors.length > 0 && (
                          <div className="validation-errors-list" role="alert">
                            <p>Requisitos de seguridad:</p>
                            <ul>
                              {passwordData.validationErrors.map((err, idx) => (
                                <li key={idx}>{err}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ) : passwordMode === u.id ? (
                      // Modo cambio de contraseña (Nielsen H1: Visibilidad del estado del sistema)
                      <div className="password-change-container">
                        <div className="password-inputs">
                          <div className="password-field-wrapper">
                            <input
                              type={passwordData.showPassword ? 'text' : 'password'}
                              placeholder="Nueva contraseña"
                              value={passwordData.password}
                              onChange={e => {
                                const pwd = e.target.value;
                                setPasswordData(prev => ({
                                  ...prev,
                                  password: pwd,
                                  validationErrors: validatePassword(pwd, prev.confirmPassword)
                                }));
                              }}
                              className={`cell-input ${
                                passwordData.password.length > 0 
                                  ? (passwordData.validationErrors.length === 0 ? 'valid' : 'invalid')
                                  : ''
                              }`}
                              aria-label="Nueva contraseña"
                              aria-describedby="password-strength"
                            />
                          </div>
                          <div className="password-field-wrapper">
                            <input
                              type={passwordData.showPassword ? 'text' : 'password'}
                              placeholder="Confirmar contraseña"
                              value={passwordData.confirmPassword}
                              onChange={e => {
                                const confPwd = e.target.value;
                                setPasswordData(prev => ({
                                  ...prev,
                                  confirmPassword: confPwd,
                                  validationErrors: validatePassword(prev.password, confPwd)
                                }));
                              }}
                              className={`cell-input ${
                                passwordData.confirmPassword.length > 0 
                                  ? (passwordData.password === passwordData.confirmPassword ? 'valid' : 'invalid')
                                  : ''
                              }`}
                              aria-label="Confirmar contraseña"
                            />
                          </div>
                          <button
                            className="toggle-visibility-btn"
                            onClick={() => setPasswordData(prev => ({ ...prev, showPassword: !prev.showPassword }))}
                            aria-label={passwordData.showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                            type="button"
                          >
                            {passwordData.showPassword ? 'Ocultar' : 'Mostrar'}
                          </button>
                        </div>
                        
                        {/* Nielsen H1: Indicador de fortaleza de contraseña */}
                        {passwordData.password.length > 0 && (
                          <div className="password-strength-indicator" id="password-strength" role="status" aria-live="polite">
                            <div className="strength-bar">
                              <div className={`strength-fill ${getPasswordStrength(passwordData.password).level}`}></div>
                            </div>
                            <span className={`strength-label ${getPasswordStrength(passwordData.password).level}`}>
                              {getPasswordStrength(passwordData.password).label}
                            </span>
                          </div>
                        )}
                        
                        {/* Nielsen H9: Mensajes de error claros y descriptivos */}
                        {passwordData.validationErrors.length > 0 && (
                          <div className="validation-errors-list" role="alert">
                            <p>Requisitos de seguridad:</p>
                            <ul>
                              {passwordData.validationErrors.map((err, idx) => (
                                <li key={idx}>{err}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="password-placeholder">•••••••• (Cifrada)</span>
                    )}
                  </td>
                  <td className="row-actions">
                    {passwordMode === u.id ? (
                      // Nielsen H3: Control y libertad del usuario (botones Guardar/Cancelar)
                      <>
                        <button 
                          className="small primary" 
                          onClick={savePasswordChange}
                          disabled={
                            passwordData.validationErrors.length > 0 || 
                            passwordData.password.length === 0 ||
                            passwordData.confirmPassword.length === 0
                          }
                          aria-label="Guardar nueva contraseña"
                        >
                          Guardar
                        </button>
                        <button 
                          className="small" 
                          onClick={cancelPasswordChange}
                          aria-label="Cancelar cambio de contraseña"
                        >
                          Cancelar
                        </button>
                      </>
                    ) : editingId === u.id ? (
                      // Nielsen H5: Prevención de errores en edición de usuario
                      <>
                        <button 
                          className="small primary" 
                          onClick={saveEdit}
                          disabled={
                            newRowId === u.id && passwordData.validationErrors.length > 0
                          }
                          aria-label="Guardar cambios"
                        >
                          Guardar
                        </button>
                        <button 
                          className="small" 
                          onClick={() => cancelEdit('cancel')}
                          aria-label="Cancelar edición"
                        >
                          Cancelar
                        </button>
                      </>
                    ) : (
                      <>
                        <button 
                          className="small btn-edit" 
                          onClick={() => startEdit(u.id)}
                          aria-label={`Editar usuario ${u.nombre}`}
                        >
                          Editar
                        </button>
                        <button 
                          className="small btn-password" 
                          onClick={() => initiatePasswordChange(u.id)}
                          aria-label={`Cambiar contraseña de ${u.nombre}`}
                        >
                          Contraseña
                        </button>
                        <button 
                          className="small danger" 
                          onClick={() => removeUser(u.id)}
                          aria-label={`Eliminar usuario ${u.nombre}`}
                        >
                          Eliminar
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', color: '#666' }}>
                    No se encontraron usuarios
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {/* Paginación */}
        {filtered.length > 0 && (
          <div className="pagination-bar">
            <button 
              className="small" 
              onClick={() => setPage(p => Math.max(1, p - 1))} 
              disabled={page === 1}
              aria-label="Página anterior"
            >
              ← Anterior
            </button>
            <span className="page-indicator" role="status">
              Página {page} de {totalPages} ({filtered.length} usuario{filtered.length !== 1 ? 's' : ''})
            </span>
            <button 
              className="small" 
              onClick={() => setPage(p => Math.min(totalPages, p + 1))} 
              disabled={page === totalPages}
              aria-label="Página siguiente"
            >
              Siguiente →
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default UsersTable;
