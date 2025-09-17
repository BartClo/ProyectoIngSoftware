# Frontend - Chatbot USS

Frontend del Chatbot para la Universidad San Sebastián desarrollado con React, TypeScript y Vite.

## ⚙️ Requisitos

- Node.js 18+
- npm o yarn
- Backend API funcionando

## 🚀 Inicio Rápido

### Desarrollo Local

1. **Configurar Variables de Entorno**
   ```bash
   # Copia el archivo de ejemplo
   cp .env.example .env
   
   # Edita .env con la URL de tu backend:
   # VITE_API_BASE_URL=http://127.0.0.1:8000  # Para desarrollo local
   ```

2. **Instalar Dependencias**
   ```bash
   cd frontend
   npm install
   ```

3. **Iniciar el Servidor de Desarrollo**
   ```bash
   npm run dev
   ```

La aplicación se ejecutará en `http://localhost:5173`.

## 🚀 Despliegue en Producción

### Vercel (Frontend)

1. **Preparar el Repositorio**
   - Asegúrate de que todos los cambios estén en Git
   - El archivo `vercel.json` ya está configurado

2. **Desplegar en Vercel**
   - Ve a [vercel.com](https://vercel.com) y crea una cuenta
   - Conecta tu repositorio de GitHub
   - Selecciona "Import Project"
   - Configura:
     - **Framework Preset**: Vite
     - **Root Directory**: `frontend`
     - **Build Command**: `npm run build`
     - **Output Directory**: `dist`

3. **Configurar Variables de Entorno en Vercel**
   ```
   VITE_API_BASE_URL=https://tu-backend-en-render.onrender.com
   ```

4. **Configurar Dominio Personalizado (Opcional)**
   - En el dashboard de Vercel, ve a Settings > Domains
   - Agrega tu dominio personalizado

### Variables de Entorno Requeridas

- `VITE_API_BASE_URL`: URL del backend API (sin barra final)

## 📦 Scripts Disponibles

- `npm run dev`: Inicia el servidor de desarrollo
- `npm run build`: Construye la aplicación para producción
- `npm run preview`: Previsualiza la build de producción
- `npm run lint`: Ejecuta el linter

## 🏗️ Estructura del Proyecto
El proyecto está estructurado de la siguiente manera:

- `src/`: Directorio principal del código fuente
  - `assets/`: Imágenes y recursos gráficos
  - `components/`: Componentes React organizados por funcionalidad
    - `auth/`: Componentes relacionados con la autenticación
    - `chat/`: Componentes para la interfaz de chat
    - `dashboard/`: Componentes para el panel principal
    - `settings/`: Componentes para la configuración
  - `App.tsx`: Componente principal que gestiona la navegación y el estado
  - `main.tsx`: Punto de entrada de la aplicación

## Inicio de sesión

Para acceder a la aplicación, usa un correo electrónico con dominio `@docente.uss.cl`. La validación del correo está implementada, pero actualmente no hay una verificación real con backend, por lo que cualquier contraseña funcionará.

## Características principales

- **Autenticación**: Inicio de sesión con correo institucional
- **Interfaz de chat**: Envía y recibe mensajes con el asistente IA
- **Historial de conversaciones**: Guarda y gestiona conversaciones previas
- **Feedback**: Posibilidad de calificar las respuestas del asistente

## Construcción para producción

Para crear una versión optimizada para producción, ejecuta:

```bash
npm run build
```

Los archivos generados se almacenarán en el directorio `dist/`.

## Tecnologías utilizadas

- [React](https://reactjs.org/) - Biblioteca JavaScript para construir interfaces de usuario
- [TypeScript](https://www.typescriptlang.org/) - Superset tipado de JavaScript
- [Vite](https://vitejs.dev/) - Herramienta de construcción y servidor de desarrollo

## Problemas conocidos

- La aplicación actualmente utiliza datos simulados para las respuestas del asistente IA
- No hay persistencia de datos entre sesiones
- La funcionalidad de feedback es demostrativa

## Contribución

Si deseas contribuir a este proyecto, por favor:

1. Haz un fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/nueva-funcionalidad`)
3. Realiza tus cambios y haz commits (`git commit -m 'Añadir nueva funcionalidad'`)
4. Sube tu rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

