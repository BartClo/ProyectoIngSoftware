# 🎯 Heurísticas de Nielsen: Gestión de Usuarios

## Paleta de Colores del Dashboard USS
- **Azul Principal**: `#002855` (Azul USS institucional)
- **Azul Hover**: `#001f40` (Versión más oscura para interacciones)
- **Blanco**: `#ffffff` (Fondo principal)
- **Gris Claro**: `#f5f7fb`, `#f9fafc` (Fondos secundarios)
- **Rojo Peligro**: `#dc3545` (Acciones destructivas)

---

## 📋 Las 10 Heurísticas de Nielsen Implementadas

### 1️⃣ **Visibilidad del Estado del Sistema** (Visibility of System Status)

**Dónde está:**
- **Toast Notifications**: Aparecen después de guardar, eliminar o cancelar acciones
  - Ubicación: Esquina inferior derecha
  - Color: Azul USS `#002855`
  - Duración: 2 segundos con animación
  
- **Badges de Estado**: 
  - "Activo" → Verde `#d4edda` con borde
  - "Inactivo" → Gris `#e8ebf2`
  
- **Estados de Edición**: 
  - Los campos cambian a inputs cuando se edita
  - Los botones cambian de "Editar/Eliminar" a "Guardar/Cancelar"

**Por qué es importante:**
El usuario siempre sabe qué está pasando en el sistema. Las acciones tienen feedback visual inmediato.

---

### 2️⃣ **Relación entre el Sistema y el Mundo Real** (Match Between System and Real World)

**Dónde está:**
- **Lenguaje natural en botones**:
  - "Nuevo Usuario" (no "Create New Record")
  - "Guardar" (no "Submit")
  - "Cancelar" (no "Abort")
  - "← Anterior" / "Siguiente →" (flechas direccionales intuitivas)

- **Placeholders descriptivos**:
  - "🔍 Buscar por nombre, correo o rol..."
  - "Contraseña" para nuevos usuarios

**Por qué es importante:**
Usa términos familiares para usuarios no técnicos, evitando jerga de programación.

---

### 3️⃣ **Control y Libertad del Usuario** (User Control and Freedom)

**Dónde está:**
- **Botón "Cancelar"** siempre visible durante edición
- **Confirmación antes de eliminar**: Modal `window.confirm()` con mensaje claro
- **Cancelar creación**: Si se cancela un nuevo usuario, se elimina la fila temporal
- **Sin auto-guardado**: El usuario decide cuándo guardar

**Por qué es importante:**
El usuario tiene control total. Puede deshacer acciones sin consecuencias permanentes.

---

### 4️⃣ **Consistencia y Estándares** (Consistency and Standards)

**Dónde está:**
- **Colores consistentes con el dashboard**:
  - Botones primarios: Azul `#002855`
  - Hover: `#001f40`
  - Bordes azules en encabezados y secciones
  
- **Tipografía uniforme**:
  - Encabezados: 20px, peso 600
  - Texto: 14px
  - Labels: 13px uppercase
  
- **Espaciado consistente**:
  - Padding: 16px, 20px, 24px (múltiplos de 4)
  - Gap entre elementos: 8px, 10px, 12px

- **Border radius**: 6px en todos los elementos interactivos

**Por qué es importante:**
La interfaz se siente cohesiva con el resto de la aplicación USS.

---

### 5️⃣ **Prevención de Errores** (Error Prevention)

**Dónde está:**
- **Validación de inputs**:
  - Placeholder con formato esperado
  - Campos de email sugieren formato
  
- **Confirmación antes de eliminar**:
  ```javascript
  if (!window.confirm('¿Eliminar usuario?')) return;
  ```

- **Estados deshabilitados claros**:
  - Botones de paginación deshabilitados cuando no aplican
  - Opacidad 0.5 + cursor `not-allowed`

- **Campo de contraseña para nuevos usuarios**:
  - Obligatorio al crear
  - Tipo `password` oculta caracteres

**Por qué es importante:**
Previene errores costosos como eliminar usuarios accidentalmente.

---

### 6️⃣ **Reconocimiento antes que Recuerdo** (Recognition Rather than Recall)

**Dónde está:**
- **Placeholders descriptivos**:
  - "🔍 Buscar por nombre, correo o rol..."
  
- **Labels visibles siempre**:
  - Encabezados de tabla: "Nombre", "Correo", "Rol", "Estado", "Acciones"
  
- **Estados visibles**:
  - Badge "Activo"/"Inactivo" siempre visible
  - No requiere recordar el estado anterior del usuario

- **Contador de resultados**:
  - "Página 1 de 3 (24 usuarios)"
  
- **Aria-labels para accesibilidad**:
  ```tsx
  aria-label="Editar usuario Juan Pérez"
  ```

**Por qué es importante:**
El usuario no necesita recordar información de pantallas anteriores.

---

### 7️⃣ **Flexibilidad y Eficiencia de Uso** (Flexibility and Efficiency of Use)

**Dónde está:**
- **Búsqueda en tiempo real**:
  - Filtra mientras escribe
  - Sin necesidad de botón "Buscar"
  
- **Edición inline**:
  - No abre modales
  - Edita directamente en la tabla
  
- **Paginación inteligente**:
  - 8 usuarios por página (evita scroll excesivo)
  - Navegación con teclado (← →)
  
- **Atajos visuales**:
  - Hover sobre filas para resaltar
  - Transiciones suaves (0.2s)

**Por qué es importante:**
Usuarios expertos pueden trabajar más rápido sin sacrificar usabilidad para novatos.

---

### 8️⃣ **Diseño Estético y Minimalista** (Aesthetic and Minimalist Design)

**Dónde está:**
- **Sin emojis en botones de acción** (Editar, Eliminar, Guardar, Cancelar)
- **Solo un emoji útil**: 🔍 en el campo de búsqueda para indicar función
- **Paleta limitada**:
  - Azul USS, blanco, gris claro
  - Rojo solo para acciones peligrosas
  
- **Espaciado generoso**:
  - Padding amplio para respirar
  - Sin elementos decorativos innecesarios
  
- **Gradientes sutiles**:
  - Encabezado: `linear-gradient(to right, #ffffff, #f9fafc)`
  - Paginación: `linear-gradient(to right, #f9fafc, #ffffff)`

- **Sombras discretas**:
  - `box-shadow: 0 4px 12px rgba(0, 40, 85, 0.1)`

**Por qué es importante:**
Cada elemento tiene un propósito. Sin distracciones visuales.

---

### 9️⃣ **Ayudar a Reconocer, Diagnosticar y Recuperarse de Errores**

**Dónde está:**
- **Mensajes de error claros**:
  - Toast: "Error creando usuario"
  - Console.error para debugging
  
- **Color rojo para acciones destructivas**:
  - Botón "Eliminar": Borde rojo `#dc3545`
  - Hover: Fondo rojo
  
- **Feedback inmediato**:
  - Border focus azul cuando input tiene foco
  - Shadow cuando hay error
  
- **Recuperación de errores**:
  - Si falla creación, la fila temporal se mantiene
  - Usuario puede reintentar sin perder datos

- **Estados de inactividad visibles**:
  - Filas inactivas con opacidad 0.6
  - Fondo gris `#f9f9f9`

**Por qué es importante:**
Cuando algo falla, el usuario sabe qué pasó y cómo solucionarlo.

---

### 🔟 **Ayuda y Documentación** (Help and Documentation)

**Dónde está:**
- **Placeholders informativos**:
  - "🔍 Buscar por nombre, correo o rol..."
  - "Contraseña" al crear usuario
  
- **Labels descriptivos**:
  - Encabezados de tabla con mayúsculas y espaciado
  - "Administración de Usuarios" como título principal
  
- **Mensajes contextuales**:
  - "No se encontraron usuarios" cuando búsqueda vacía
  - "Página X de Y (N usuarios)" para orientación
  
- **Aria-labels para screen readers**:
  ```tsx
  aria-label="Campo de búsqueda de usuarios"
  aria-label="Crear nuevo usuario"
  aria-label="Editar usuario María González"
  ```

- **Este documento**:
  - Explica cada heurística aplicada
  - Ubicación específica en el código

**Por qué es importante:**
Usuarios nuevos pueden entender la interfaz sin necesidad de capacitación.

---

## 📁 Archivos Relacionados

- **users-table.tsx**: Componente principal con lógica
- **users-table.css**: Estilos aplicando heurísticas

---

**Fecha de implementación**: 31 de octubre de 2025  
**Diseñador**: GitHub Copilot  
**Basado en**: 10 Heurísticas de Usabilidad de Jakob Nielsen
