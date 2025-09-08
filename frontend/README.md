# Asistente IA USS - Frontend

## Descripción

Este proyecto es la interfaz de usuario para el Asistente IA de la Universidad San Sebastián. La aplicación proporciona una interfaz de chat interactiva que permite a los usuarios (principalmente profesores) realizar consultas y recibir respuestas del asistente virtual.

## Requisitos previos

- [Node.js](https://nodejs.org/) (versión 16 o superior)
- [npm](https://www.npmjs.com/) (incluido con Node.js)
- Conexión a Internet para descargar las dependencias

## Instalación

Sigue estos pasos para instalar y configurar el proyecto en tu entorno local:

1. Clona el repositorio desde GitHub:

```bash
git clone https://github.com/BartClo/ProyectoIngSoftware.git
```

2. Cambia al directorio del frontend:

```bash
cd ProyectoIngSoftware/frontend
```

3. Cambia a la rama feature/frontend:

```bash
git checkout feature/frontend
```

4. Instala las dependencias del proyecto:

```bash
npm install
```

## Ejecución del proyecto

Una vez instaladas las dependencias, puedes iniciar el servidor de desarrollo con el siguiente comando:

```bash
npm run dev
```

Esto iniciará la aplicación en modo de desarrollo. Abre [http://localhost:5173](http://localhost:5173) en tu navegador para verla.
```

## Estructura del proyecto

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

