import { useMemo, useState } from 'react';
import './users-table.css';

type Role = 'admin' | 'docente' | 'estudiante';

export interface UserRow {
  id: string;
  nombre: string;
  email: string;
  rol: Role;
  activo: boolean;
}

const seedUsers: UserRow[] = [
  { id: 'u1', nombre: 'Ana Pérez', email: 'ana.perez@docente.uss.cl', rol: 'docente', activo: true },
  { id: 'u2', nombre: 'Juan Soto', email: 'juan.soto@admin.uss.cl', rol: 'admin', activo: true },
  { id: 'u3', nombre: 'María López', email: 'maria.lopez@docente.uss.cl', rol: 'docente', activo: false },
];

const UsersTable: React.FC = () => {
  const [users, setUsers] = useState<UserRow[]>(seedUsers);
  const [query, setQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<Partial<UserRow>>({});

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return users;
    return users.filter(u =>
      u.nombre.toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q) ||
      u.rol.toLowerCase().includes(q)
    );
  }, [users, query]);

  const startEdit = (id: string) => {
    const u = users.find(x => x.id === id);
    if (!u) return;
    setEditingId(id);
    setDraft({ ...u });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setDraft({});
  };

  const saveEdit = () => {
    if (!editingId) return;
    setUsers(prev => prev.map(u => (u.id === editingId ? { ...(u as UserRow), ...(draft as UserRow), id: u.id } : u)));
    // Notificación en-app
    showToast('Usuario actualizado correctamente');
    cancelEdit();
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
    setUsers(prev => prev.filter(u => u.id !== id));
    showToast('Usuario eliminado');
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
    setUsers(prev => [nuevo, ...prev]);
    setEditingId(id);
    setDraft({ ...nuevo });
    showToast('Usuario creado');
  };

  return (
    <div className="admin-wrapper">
      <div className="admin-card">
        <div className="admin-card-header">
          <h2>Administración de Usuarios</h2>
          <div className="actions">
            <input
              className="search"
              placeholder="Buscar por nombre, correo o rol"
              value={query}
              onChange={e => setQuery(e.target.value)}
            />
            <button className="primary" onClick={addUser}>+ Nuevo</button>
          </div>
        </div>

        <div className="table-scroll">
          <table className="users-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Correo</th>
                <th>Rol</th>
                <th>Estado</th>
                <th style={{ width: 150 }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(u => (
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
                        <option value="estudiante">Estudiante</option>
                      </select>
                    ) : (
                      u.rol.charAt(0).toUpperCase() + u.rol.slice(1)
                    )}
                  </td>
                  <td>
                    {editingId === u.id ? (
                      <select
                        className="cell-input"
                        value={String(draft.activo ?? true)}
                        onChange={e => setDraft(d => ({ ...d, activo: e.target.value === 'true' }))}
                      >
                        <option value="true">Activo</option>
                        <option value="false">Inactivo</option>
                      </select>
                    ) : (
                      <span className={u.activo ? 'badge success' : 'badge'}>
                        {u.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    )}
                  </td>
                  <td className="row-actions">
                    {editingId === u.id ? (
                      <>
                        <button className="small primary" onClick={saveEdit}>Guardar</button>
                        <button className="small" onClick={cancelEdit}>Cancelar</button>
                      </>
                    ) : (
                      <>
                        <button className="small" onClick={() => startEdit(u.id)}>Editar</button>
                        <button className="small danger" onClick={() => removeUser(u.id)}>Eliminar</button>
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
      </div>
    </div>
  );
};

export default UsersTable;
