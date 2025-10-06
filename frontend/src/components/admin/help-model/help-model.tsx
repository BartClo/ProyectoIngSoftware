import React from 'react';
import './help-model.css';

interface AdminHelpModelProps {
  onClose: () => void;
}

const AdminHelpModel: React.FC<AdminHelpModelProps> = ({ onClose }) => {
  return (
    <div className="help-model-overlay">
      <div className="help-model-container">
        <div className="help-model-header">
          <h2>Ayuda - Panel de Administración</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div className="help-model-content">
          <div className="help-section">
            <h3>Vistas disponibles</h3>
            <ul className="help-list">
              <li><strong>Administración de usuarios:</strong> Crear, editar y eliminar usuarios. Usa “+ Nuevo” para agregar y “Cancelar” para descartar.</li>
              <li><strong>Reportes:</strong> Revisa reportes de problemas. Usa el botón “...” para abrir el editor, cambiar estado y registrar comentario de solución.</li>
              <li><strong>Crear conversación:</strong> Inicia una conversación en nombre de un usuario (ingresa título y correo).</li>
            </ul>
          </div>

          <div className="help-section">
            <h3>Controles y navegación</h3>
            <ul className="help-list">
              <li>Los listados usan paginación para evitar scroll vertical.</li>
              <li>El botón activo del encabezado se resalta en azul, los demás permanecen blancos.</li>
              <li>En reportes, puedes filtrar por estado (Todos, Pendiente, Resuelto) y buscar por docente, correo, tipo o comentario.</li>
            </ul>
          </div>

          <div className="help-section">
            <h3>Buenas prácticas</h3>
            <ul className="help-list">
              <li>Guarda los cambios al editar reportes para que el estado y comentario queden registrados.</li>
              <li>Usa “Cancelar” en la creación de usuarios para evitar entradas incompletas.</li>
              <li>Verifica correos antes de crear una conversación.</li>
            </ul>
          </div>
        </div>

        <div className="help-model-footer">
          <button className="help-close-button" onClick={onClose}>Cerrar</button>
        </div>
      </div>
    </div>
  );
};

export default AdminHelpModel;
