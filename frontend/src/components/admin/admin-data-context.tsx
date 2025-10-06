import React, { createContext, useContext, useState } from 'react';

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

const initialReports: AdminReport[] = [
  { id: '1', docente: 'Ana Pérez', email: 'ana.perez@docente.uss.cl', tipo: 'Información incorrecta', comentario: 'Respuesta desactualizada en tema X', fechaEnvio: '2025-10-01', estado: 'pendiente' },
  { id: '2', docente: 'Juan Soto', email: 'juan.soto@docente.uss.cl', tipo: 'Contenido inapropiado', comentario: 'Lenguaje poco adecuado en la respuesta', fechaEnvio: '2025-10-03', estado: 'pendiente' },
  { id: '3', docente: 'María López', email: 'maria.lopez@docente.uss.cl', tipo: 'Error del sistema', comentario: 'No carga historial de conversación', fechaEnvio: '2025-10-04', estado: 'resuelto', adminComentario: 'Se corrigió el bug en backend' },
];

interface AdminDataContextValue {
  users: UserRow[];
  setUsers: React.Dispatch<React.SetStateAction<UserRow[]>>;
  reports: AdminReport[];
  setReports: React.Dispatch<React.SetStateAction<AdminReport[]>>;
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
  return (
    <AdminDataContext.Provider value={{ users, setUsers, reports, setReports }}>
      {children}
    </AdminDataContext.Provider>
  );
};
