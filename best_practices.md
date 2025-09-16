# 📘 Project Best Practices

## 1. Project Purpose
Chatbot para docentes de la Universidad San Sebastián. El sistema ofrece una interfaz web (React + Vite) para conversar con un asistente IA que responde basándose en documentos PDF cargados (RAG). El backend (FastAPI + PostgreSQL) maneja autenticación básica de usuarios, extracción/segmentación de documentos, embeddings con Gemini, búsqueda semántica con FAISS y generación de respuestas condicionadas al contexto.

## 2. Project Structure
- Raíz
  - `backend/`
    - `main.py`: FastAPI app; endpoints: registro/login, chat con RAG, reconstrucción de índice, health de IA y depuración de recuperación.
    - `database.py`: Configuración de SQLAlchemy (engine, Base, SessionLocal, get_db).
    - `models.py`: Modelos ORM (User).
    - `rag_service.py`: Pipeline alternativo con LangChain + OpenAI + FAISS. Actualmente independiente del flujo de `main.py`.
    - `context_docs/`: PDFs fuente para construir el índice RAG.
    - `vector_store.index` y `docstore.pkl`: artefactos generados por FAISS/docstore.
    - `requirements.txt`: Dependencias de backend.
    - `README.md`: Guía de backend.
  - `frontend/`
    - `src/`
      - `components/` (por funcionalidad):
        - `auth/` (login)
        - `dashboard/`
        - `chat/` (sidebar, interface, no-conversation, report/help modals)
        - `settings/` (modal de configuración)
        - `theme/` (contexto de tema y fuente)
      - `assets/` (imágenes/SVGs)
      - `App.tsx`, `main.tsx`
    - Configuración: `package.json`, `vite.config.ts`, `eslint.config.js`, `tsconfig*.json`
    - `README.md`: Guía de frontend
  - `db/`: Placeholder para SQL/init (referenciado por docker compose)
  - `ia/`: Placeholder para módulos/volúmenes de IA de compose
  - `docker.compose.yml`: Orquestación de servicios (ver nota de nombre más abajo)
  - `README.md`: README raíz

Notas:
- Considerar renombrar `docker.compose.yml` a `docker-compose.yml` (nombre estándar reconocido por Docker Compose).
- El backend usa `http://localhost:5173` en CORS para Vite (desarrollo). Alinear puertos con Docker si se usa `3000`.

## 3. Test Strategy
Actualmente no hay tests. Recomendación:
- Backend (Python/FastAPI):
  - Framework: `pytest` + `httpx`/`fastapi.testclient` para pruebas de endpoints.
  - Estructura: `backend/tests/` con `test_*.py`. Separar unit (servicios, utilidades) vs integration (endpoints + DB).
  - Mocking: usar `unittest.mock`/`pytest-mock` para externalidades (DB, Gemini, FAISS). Para RAG, fijar embeddings o usar fixtures con índices pequeños.
  - Cobertura: apuntar a 80%+. Excluir artefactos generados y ficheros de arranque si aplica.
- Frontend (React + TS):
  - Framework: `Jest` + `@testing-library/react`.
  - Estructura: `frontend/src/**/__tests__/*.(test|spec).tsx` o colocalizados `*.test.tsx`.
  - Mocking: mock de fetch/API, localStorage y timers. Probar componentes con hooks (ThemeProvider) envolviendo en providers.
  - E2E opcional: `Playwright` o `Cypress` para flujos críticos (login, crear conversación, enviar mensaje).

Filosofía:
- Unit tests para lógica pura (chunking, helpers, validación).
- Integration tests para endpoints principales (`/login`, `/chat`, `/rebuild_index`).
- E2E para el flujo completo usuario.

## 4. Code Style
Backend (Python/FastAPI):
- Tipado: usar `typing` y `pydantic` para request/response models. Mantener funciones `async def` cuando se hagan IO; si la librería es síncrona, ejecutarla en threadpool (`anyio.to_thread.run_sync`) para no bloquear el event loop.
- Configuración: no hardcodear `DATABASE_URL` en código. Cargar desde variables de entorno (`os.getenv`) o archivo `.env` (p. ej. `python-dotenv`). Mismo para `GEMINI_API_KEY`.
- Rutas y routers: preferir organizar endpoints por routers (`APIRouter`) y módulos por dominio (auth, chat, admin).
- Errores: usar `HTTPException` y handlers globales para errores comunes. Loguear excepciones de proveedores externos; devolver mensajes seguros al cliente.
- Persistencia de artefactos: escribir índices FAISS/docstore en rutas predecibles y con chequeos de consistencia (ya implementado). No bloquear el arranque si un PDF falla (ya implementado); loguear.
- Seguridad: contraseñas con `passlib` (ok). Implementar JWT real en `/login` (no devolver email como token). Manejar CORS por entorno (desarrollo vs producción).

Frontend (React + TS):
- Componentes: funciones con hooks. Tipar props y estados. Extraer tipos compartidos a `types.ts` por feature.
- Estado: `useState/useEffect` para local. Considerar `useReducer` para flows complejos y custom hooks para lógica compartida (p. ej. `useConversations`).
- Estilos: CSS por componente ya usado. Mantener naming consistente BEM o variantes.
- Nombres: 
  - Componentes/archivos: PascalCase (`Login.tsx`, `DashboardHeader.tsx`). Directorios de componentes en kebab-case o PascalCase, pero consistentes.
  - Variables/funciones: camelCase.
  - Idioma: unificar (idealmente inglés en código, español en UI). Hay mezcla actual (`help-model`, `reporte-model`, `report-modal`). Normalizar.
- Accesibilidad: usar `aria-*` (se aplica en botones). Incluir labels y roles cuando corresponda.
- API: centralizar llamadas en un cliente (`frontend/src/lib/api.ts`) con manejo de errores, timeouts y tipado de DTOs. Evitar llamadas directas desde componentes.

Comentarios/Docs:
- Mantener comentarios breves y actualizados. Usar README por paquete.
- Añadir docstrings a funciones utilitarias y servicios relevantes.

## 5. Common Patterns
- RAG:
  - Segmentación de texto con `_chunk_text` y almacenamiento de chunks.
  - Embeddings con Gemini (`embedding-001`) y vector store FAISS normalizado con IP para coseno. Umbral de similitud configurable.
  - Sugerencias de tópicos cuando la consulta es genérica o no hay contexto suficiente.
  - Artefactos persistentes (`vector_store.index`, `docstore.pkl`) validados al arranque.
- OCR como fallback: si un PDF no tiene texto, se renderiza y procesa con Tesseract (`pypdfium2` + `pytesseract`).
- Frontend:
  - Almacenamiento de conversaciones en `localStorage` con restauración de fechas a `Date` y autoscroll.
  - Contexto de tema/tamaño de fuente (`ThemeProvider`) con persistencia en `localStorage`.
- Orquestación (Compose): servicios `frontend`, `backend`, `ia`, `db` con volúmenes. Alinear puertos con Vite/Swagger en local.

Recomendaciones de patrón:
- Backend: extraer servicios (embedding, retrieval, generación) a módulos con interfaces claras para permitir swapping de proveedores (Gemini/OpenAI/local). Aplicar patrón Adapter para providers.
- Frontend: mover lógica de conversación a hook (`useChat`) y separar presentación/estado.

## 6. Do's and Don'ts
✅ Do's
- Usar variables de entorno para secretos y configuraciones (GEMINI_API_KEY, DATABASE_URL, proveedores de IA).
- Validar entradas con modelos Pydantic y sanitizar prompts.
- Manejar timeouts/reintentos contra servicios externos (embeddings/generación).
- Versionar solo código fuente; ignorar artefactos generados (índices FAISS, pickles, builds, `.pkl`, `.index`).
- Escribir tests para piezas críticas: login, chat retrieval, construcción de índice, almacenamiento local de conversaciones.
- Mantener consistencia de nombres y estructura por feature.
- Implementar JWT para auth real y usar `Depends` para rutas protegidas.

❌ Don'ts
- No hardcodear credenciales/URLs en el código (actualmente `DATABASE_URL` está hardcodeada en `database.py`).
- No bloquear el thread de eventos con llamadas síncronas pesadas dentro de endpoints async.
- No mezclar idiomas en nombres de archivos/componentes.
- No commitear artefactos generados o datos sensibles.
- No retornar tokens inseguros (como email) en autenticación.

## 7. Tools & Dependencies
- Backend
  - FastAPI, Uvicorn: API y servidor ASGI.
  - SQLAlchemy, psycopg2-binary: ORM y driver PostgreSQL.
  - Passlib[bcrypt]: hashing de contraseñas.
  - Pydantic: validación/serialización.
  - google-generativeai: embeddings y generación con Gemini.
  - FAISS, numpy: vector store y normalización.
  - pypdf, pypdfium2, pytesseract, Pillow: extracción de texto y OCR.
  - LangChain (en `rag_service.py`): alternativa con OpenAI/FAISS (no integrada en `main.py`).
- Frontend
  - React 19, TypeScript, Vite.
  - ESLint base (JS/TS/React hooks/refresh) y configs TS.

Setup backend (local):
- Python 3.9+ y venv
- `pip install -r backend/requirements.txt`
- Variables de entorno: `GEMINI_API_KEY`, `DATABASE_URL` (p. ej. `postgresql://user:pass@localhost/db`)
- Crear DB y correr `uvicorn backend.main:app --reload`

Setup frontend (local):
- `npm install` dentro de `frontend/`
- `npm run dev` y abrir `http://localhost:5173`

Docker Compose:
- Alinear nombre del archivo y puertos. Variables: `DATABASE_URL` en backend, volumen de `db`, volumen `ia` si aplica. Considerar añadir `.env` y `env_file`.

## 8. Other Notes
- UI y textos en español. Mantener consistencia lingüística en la interfaz.
- El endpoint `/chat/` aplica un umbral de similitud y fallback a top-k; respetar esta lógica al modificar retrieval.
- Si no hay documentos o embeddings fallan, el sistema devuelve sugerencias de temas; no reemplazar por alucinaciones.
- Considerar mover `vector_store.index` y `docstore.pkl` a un directorio de datos fuera del repo o ignorarlos en `.gitignore`.
- `rag_service.py` y `main.py` usan proveedores diferentes (OpenAI vs Gemini). Unificar proveedor o parametrizar.
- Implementar cliente HTTP tipado en frontend y normalizar rutas de API; manejar CORS por entorno.
- Seguridad: implementar JWT con expiración y refresh; almacenar tokens en `httpOnly` cookies o almacenamiento seguro; proteger rutas backend con `Depends`.
- OCR: `pytesseract` requiere binario Tesseract instalado en el sistema. Documentar instalación por SO y configurar `TESSDATA_PREFIX` si es necesario.
- Producción: configurar logging estructurado, límites de tamaño de archivo PDF, limpieza de artefactos antiguos y estrategias de reindexación.
