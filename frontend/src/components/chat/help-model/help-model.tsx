import React from 'react';
import './help-model.css';
import robotImage from '../../../assets/chat/Robot.svg';

interface HelpModelProps {
  onClose: () => void;
}

const HelpModel: React.FC<HelpModelProps> = ({ onClose }) => {
  return (
    <div className="help-model-overlay">
      <div className="help-model-container">
        <div className="help-model-header">
          <h2>Ayuda - Asistente IA USS</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>
        
        <div className="help-model-content">
          <div className="help-intro">
            <img src={robotImage} alt="Robot IA" className="help-robot-image" />
            <p>
              El Asistente IA USS está diseñado para ayudarte en tus consultas académicas,
              administrativas y proporcionar información relevante de la universidad.
            </p>
          </div>
          
          <div className="help-section">
            <h3>¿Cómo usar el asistente?</h3>
            <ol className="help-list">
              <li>Crea una nueva conversación usando el botón "Nueva conversación"</li>
              <li>Escribe tu pregunta o solicitud en el campo de texto</li>
              <li>Presiona Enter o el botón de enviar para recibir una respuesta</li>
              <li>Puedes continuar la conversación haciendo preguntas adicionales</li>
            </ol>
          </div>
          
          <div className="help-section">
            <h3>Funcionalidades</h3>
            <ul className="help-list">
              <li><strong>Crear conversación:</strong> Inicia un nuevo chat con el asistente</li>
              <li><strong>Renombrar conversación:</strong> Cambia el título haciendo clic en el ícono de editar</li>
              <li><strong>Eliminar conversación:</strong> Elimina un chat usando el ícono de papelera</li>
              <li><strong>Buscar conversaciones:</strong> Filtra conversaciones existentes por texto</li>
            </ul>
          </div>
          
          <div className="help-section">
            <h3>Preguntas frecuentes</h3>
            <div className="faq-item">
              <h4>¿Qué tipo de preguntas puedo hacer?</h4>
              <p>
                Puedes realizar consultas académicas, sobre programas de estudio,
                procedimientos administrativos, fechas importantes, y más información
                relacionada con la documentación.
              </p>
            </div>
            <div className="faq-item">
              <h4>¿Se guardan mis conversaciones?</h4>
              <p>
                Las conversaciones se almacenan localmente en tu navegador para que 
                puedas retomarlas en el futuro. No se comparten con otros usuarios.
              </p>
            </div>
            <div className="faq-item">
              <h4>¿Cómo puedo reportar un problema?</h4>
              <p>
                Selecciona los tres puntos de la conversación (···) indicando el problema.
              </p>
            </div>
          </div>
        </div>
        
        <div className="help-model-footer">
          <button className="help-close-button" onClick={onClose}>Cerrar</button>
        </div>
      </div>
    </div>
  );
};

export default HelpModel;
