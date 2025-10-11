import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { fetchUsers, getToken } from '../../lib/api';

export type Role = 'admin' | 'docente';

export interface UserRow {
  id: string;
  nombre: string;
  email: string;
  rol: Role;
  activo: boolean;
}

const initialUsers: UserRow[] = [
  { id: 'u1', nombre: 'Ana Pérez', email: 'ana.perez@docente.uss.cl', rol: 'docente', activo: true },
  { id: 'u2', nombre: 'Juan Soto', email: 'juan.soto@admin.uss.cl', rol: 'admin', activo: true },
  { id: 'u3', nombre: 'María López', email: 'maria.lopez@docente.uss.cl', rol: 'docente', activo: false },
];

export type ReportStatus = 'pendiente' | 'resuelto';

export interface AdminReport {
  id: string;
  docente: string; // se usa para fallback, el nombre visible se tomará del usuario si existe
  email: string;
  tipo: string;
  comentario: string;
  fechaEnvio: string;
  estado: ReportStatus;
  adminComentario?: string;
}

const initialReports: AdminReport[] = [];

interface AdminDataContextValue {
  users: UserRow[];
  setUsers: React.Dispatch<React.SetStateAction<UserRow[]>>;
  reports: AdminReport[];
  setReports: React.Dispatch<React.SetStateAction<AdminReport[]>>;
  refreshUsers: () => Promise<void>;
}

const AdminDataContext = createContext<AdminDataContextValue | undefined>(undefined);

export const useAdminData = (): AdminDataContextValue => {
  const ctx = useContext(AdminDataContext);
  if (!ctx) throw new Error('useAdminData debe usarse dentro de AdminDataProvider');
  return ctx;
};

export const AdminDataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [users, setUsers] = useState<UserRow[]>(initialUsers);
  const [reports, setReports] = useState<AdminReport[]>(initialReports);

  const refreshReports = useCallback(async () => {
    try {
      const token = getToken();
      if (!token) return;
      const res: any = await (await import('../../lib/api')).listAdminReports();
      if (Array.isArray(res)) {
        const mapped = res.map((r: any) => ({ id: String(r.id), docente: r.docente || '', email: r.email || '', tipo: r.tipo || '', comentario: r.comentario || '', fechaEnvio: r.fechaEnvio || new Date().toISOString(), estado: r.estado || 'pendiente' }));
        setReports(mapped);
      }
    } catch (e) {
      // ignore
    }
  }, []);

  const refreshUsers = useCallback(async () => {
    try {
      const token = getToken();
      if (!token) return; // no autenticado
      const res: any = await fetchUsers();
      if (Array.isArray(res)) {
        const mapped = res.map((u: any) => ({ id: String(u.id), nombre: u.nombre || u.email.split('@')[0], email: u.email, rol: (u.email.endsWith('@admin.uss.cl') ? 'admin' : 'docente') as any, activo: Boolean(u.activo) }));
        setUsers(mapped);
      }
    } catch (e) {
      // mantener estado local si falla
    }
  }, []);

  useEffect(() => {
    // Intentar cargar usuarios reales del backend sólo si hay token
    refreshUsers();
    refreshReports();
    // Escuchar eventos de login global para forzar refresh si el token llega después
    const handler = () => { refreshUsers().catch(() => {}); };
    window.addEventListener('auth:login', handler as EventListener);
    return () => { window.removeEventListener('auth:login', handler as EventListener); };
  }, [refreshUsers]);
  return (
    <AdminDataContext.Provider value={{ users, setUsers, reports, setReports, refreshUsers }}>
      {children}
    </AdminDataContext.Provider>
  );
};
