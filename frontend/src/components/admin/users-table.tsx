import React, { useEffect, useMemo, useState } from 'react';
import './users-table.css';
import { useAdminData } from './admin-data-context';
import { createAdminUser } from '../../lib/api';

type Role = 'admin' | 'docente';

export interface UserRow {
  id: string;
  nombre: string;
  email: string;
  rol: Role;
  activo: boolean;
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
  // Para manejar creación
  const [newRowId, setNewRowId] = useState<string | null>(null);

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
      const payload = { email: draft.email as string, password: (draft.password || 'changeme123'), nombre: draft.nombre as string };
      createAdminUser(payload).then(() => {
        refreshUsers().then(() => {
          showToast('Usuario creado');
          setNewRowId(null);
          cancelEdit('save');
        });
      }).catch((e) => {
        console.error('create user', e);
        alert('Error creando usuario');
      });
      return;
    }
    const updated = users.map(u => (u.id === editingId ? { ...(u as UserRow), ...(draft as UserRow), id: u.id } : u));
    setUsers(updated);
    setUsersCtx(updated);
    // Notificación en-app
    showToast('Usuario actualizado correctamente');
    cancelEdit('save');
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
                <th>{newRowId ? 'Contraseña' : 'Estado'}</th>
                <th style={{ width: 150 }}>Acciones</th>
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
                      />
                    ) : (
                      u.nombre
                    )}
                  </td>
                  <td>
                    {editingId === u.id ? (
                      <input
                        className="cell-input"
                        value={String(draft.email ?? '')}
                        onChange={e => setDraft(d => ({ ...d, email: e.target.value }))}
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
                      >
                        <option value="admin">Administrador</option>
                        <option value="docente">Docente</option>
                      </select>
                    ) : (
                      u.rol.charAt(0).toUpperCase() + u.rol.slice(1)
                    )}
                  </td>
                  <td>
                    {editingId === u.id ? (
                      // Si es la fila nueva, mostrar input de contraseña en lugar del selector de estado
                      (newRowId && editingId === newRowId) ? (
                        <input
                          className="cell-input"
                          type="password"
                          placeholder="Contraseña"
                          value={String(draft.password ?? '')}
                          onChange={e => setDraft(d => ({ ...d, password: e.target.value }))}
                        />
                      ) : (
                        <select
                          className="cell-input"
                          value={String(draft.activo ?? true)}
                          onChange={e => setDraft(d => ({ ...d, activo: e.target.value === 'true' }))}
                        >
                          <option value="true">Activo</option>
                          <option value="false">Inactivo</option>
                        </select>
                      )
                    ) : (
                      <span className={u.activo ? 'badge success' : 'badge'}>
                        {u.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    )}
                  </td>
                  <td className="row-actions">
                    {editingId === u.id ? (
                      <>
                        <button 
                          className="small primary" 
                          onClick={saveEdit}
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
                          className="small" 
                          onClick={() => startEdit(u.id)}
                          aria-label={`Editar usuario ${u.nombre}`}
                        >
                          Editar
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
