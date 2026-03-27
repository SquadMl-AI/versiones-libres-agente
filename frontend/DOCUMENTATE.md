# 📚 DOCUMENTACIÓN - Proyecto Memorias 975 Frontend

---

## 🎯 ¿Qué es este proyecto?

**Memorias 975** es una aplicación web interactiva desarrollada con **React + Vite** que funciona como un asistente inteligente especializado en la **Ley 975 de Colombia** (Ley de Justicia y Paz). 

La aplicación permite a los usuarios buscar, explorar y analizar información sobre sentencias y documentos relacionados con esta ley mediante:
- 💬 Un chatbot conversacional impulsado por IA
- 🔍 Búsqueda inteligente (simple y avanzada)
- 📊 Visualización de relaciones entre documentos (grafos)
- 📈 Dashboard con métricas y estadísticas
- 📄 Visor integrado de PDF
- 🤝 Síntesis automática de información

---

## 🎯 Finalidad del Proyecto

1. **Democratizar el acceso** a información jurídica sobre la Ley 975
2. **Facilitar búsquedas inteligentes** en un corpus grande de sentencias
3. **Generar síntesis automáticas** que resumen información compleja
4. **Visualizar relaciones** entre documentos y conceptos mediante grafos
5. **Proporcionar análisis y métricas** sobre el uso y contenido de la información
6. **Mantener trazabilidad** del uso a través de feedback y ratings

---

## 🏗️ Estructura del Proyecto

```
frontend/
├── 📄 package.json              # Dependencias y scripts de npm
├── 📄 vite.config.js           # Configuración de Vite (bundler)
├── 📄 eslint.config.js         # Configuración de ESLint
├── 📄 dockerfile               # Configuración Docker
├── 📄 deploy_acr.sh            # Script de deploy a Azure Container Registry
├── 📄 index.html               # HTML principal
├── 📄 README.md                # Instrucciones básicas
│
├── 📁 public/
│   ├── vis-network.css         # Estilos para visualización de grafos
│   └── vis-network.min.js      # Librería para grafos
│
└── 📁 src/
    ├── 📄 main.jsx             # Punto de entrada de React
    ├── 📄 App.jsx              # Componente principal (orquesta toda la app)
    ├── 📄 api.js               # Cliente API (llamadas al backend)
    ├── 📄 setup-pdf.js         # Configuración del visor de PDF
    ├── 📄 App.css              # Estilos globales
    ├── 📄 index.css            # Estilos base
    │
    ├── 📁 config/
    │   ├── enviroment.js       # Variables de entorno
    │   └── msalConfig.js       # Configuración de Azure MSAL (autenticación)
    │
    ├── 📁 schemas/
    │   └── kb_id_to_name.json  # Mapeo de IDs de documentos a nombres
    │
    ├── 📁 assets/              # Recursos estáticos (imágenes, etc.)
    │
    └── 📁 components/          # Componentes React reutilizables
        ├── App.jsx             # Orquestador principal
        ├── ChatTab.jsx         # Pestaña de chat (chatbot)
        ├── SimpleSearchTab.jsx  # Pestaña de búsqueda simple
        ├── SherlockTab.jsx     # Búsqueda avanzada/sherlock
        ├── DashboardTab.jsx    # Pestaña de métricas y análisis
        ├── AboutTab.jsx        # Pestaña "Acerca de"
        ├── TermsOfUse.jsx      # Términos de uso
        ├── EmailPrompt.jsx     # Modal para capturar email del usuario
        ├── GraphViewer.jsx     # Visor de grafos (relaciones)
        ├── VisNetworkGraph.jsx # Componente de visualización con Vis Network
        ├── MessageIA.jsx       # Componente para mensajes del chatbot
        ├── MultiSelect.jsx     # Component multiselect reutilizable
        └── StarRating.jsx      # Componente de rating con estrellas
```

---

## 📦 Dependencias Principales

### Frontend Framework
- **React 19.1.0** - Librería de UI
- **React DOM 19.1.0** - Renderización en navegador
- **Vite 6.3.5** - Bundler moderno y servidor de desarrollo

### Autenticación
- **@azure/msal-browser 4.15.0** - Autenticación con Azure AD
- **@azure/msal-react 3.0.15** - Hook de React para MSAL

### Visualización de Datos
- **Recharts 3.0.2** - Gráficos (dashboard)
- **Vis Network 9.1.12** - Grafos interactivos
- **@neo4j-nvl/\*** - Visualización avanzada de grafos Neo4j

### Componentes UI
- **Ant Design (antd) 5.26.5** - Librería de componentes UI
- **motion 12.23.6** - Animaciones suaves

### Procesamiento De Documentos
- **@react-pdf-viewer/core 3.12.0** - Visor de PDF
- **pdfjs-dist 3.11.174** - Motor de renderización de PDF

### Procesamiento De Texto
- **react-markdown 10.1.0** - Renderizar markdown
- **remark-gfm 4.0.1** - Soporte de GitHub Flavored Markdown
- **stopwords-es 0.3.0** - Palabras vacías en español

---

## 🔧 Componentes Principales

### **App.jsx**
El corazón de la aplicación. Orquesta:
- Autenticación con Azure MSAL
- Gestión de estado global (búsquedas, mensajes, grafos, síntesis)
- Navegación entre pestañas
- Validación de email del usuario

**Estado Global Manejado:**
- `messages` - Historial de chat
- `query` - Consulta actual
- `results` - Resultados de búsqueda
- `graph` - Datos del grafo visualizado
- `synthesis` - Síntesis generada por IA
- `selectedValue` - Modelo LLM seleccionado

---

### **Pestaña Chat (ChatTab.jsx)**
Chatbot conversacional inteligente.
- Interfaz de conversación en tiempo real
- Envío de mensajes con Enter
- Soporte para múltiples modelos LLM
- Visor de PDF integrado en PDF viewer
- Capacidad de fullscreen para PDFs
- Manejo de sesiones continuadas

**Características:**
- Integración con visor de PDF embebido
- Respuestas contextuales

---

### **Pestaña Búsqueda Simple (SimpleSearchTab.jsx)**
Búsqueda y análisis de documentos.
- Campo de búsqueda con autocompletado
- Presencia de chunks (fragmentos) relevantes
- Síntesis de resultados con streaming
- Visualización de grafo de relaciones
- **Sistema de feedback:**
  - Rating de relevancia (1-5 estrellas) para cada resultado
  - Rating de grafos y síntesis
  - Comentarios asociados
  - Categorización de relevancia

**Funcionalidades Avanzadas:**
- Filtrado por documentos y colecciones
- Resaltado de términos en resultados
- Navegación entre chunks
- Exportación de síntesis

---

### **Pestaña Búsqueda Avanzada (SherlockTab.jsx)**
Búsqueda compleja y análisis profundo.
- Filtros avanzados
- Búsqueda por metadatos
- Análisis detallado de relevancia

---

### **Pestaña Dashboard (DashboardTab.jsx)**
Métricas y análisis del sistema.
- Gráficos de línea (tendencias)
- Gráficos de barras (comparativas)
- Gráficos de pastel (distribuciones)
- Cargas de datos en tiempo real desde el backend

**Métricas Típicas:**
- Usuarios activos
- Búsquedas realizadas
- Documentos accedidos
- Ratings promedio

---

### **Componentes Visualización**

**GraphViewer.jsx & VisNetworkGraph.jsx**
- Visualización interactiva de relaciones entre documentos
- Nodos y aristas configurables
- Física de layout automática
- Interactividad (zoom, pan, click)

**VisNetworkGraph.jsx** - Específicamente para Vis Network:
- Grafo de red interactivo
- Nodos coloreados por tipo
- Aristas que representan relaciones

---

### **Componentes Auxiliares**

| Componente | Función |
|-----------|---------|
| **EmailPrompt.jsx** | Modal para capturar email del usuario al inicio |
| **MessageIA.jsx** | Renderiza mensajes del chatbot con markdown |
| **MultiSelect.jsx** | Selector múltiple personalizado |
| **StarRating.jsx** | Rating interactivo de 1-5 estrellas |
| **AboutTab.jsx** | Información sobre el proyecto |
| **TermsOfUse.jsx** | Términos y condiciones |

---

## 🔌 API (api.js)

Módulo cliente que comunica con el backend en `http://localhost:8765` (configurable).

### Funciones Principales

```javascript
// Búsqueda simple
simpleSearch(query, llmModel, topK, maxLlmChunks, userEmail)

// Síntesis de información
synthesizeFinal(payload)
synthesizeFinalStream(payload, onChunk)  // Con streaming

// Chat
chat(messages, userEmail)
chatStream(messages, onChunk, userEmail)

// Relevancia
computeRelevance(payload)

// Feedback
sendFeedback(payload)

// Métricas
getDashboardMetrics()

// Búsqueda avanzada (Sherlock)
advancedSearch(payload, userEmail)

// Fetch de datos
fetchData(endpoint)
```

---

## 🔐 Autenticación (Azure MSAL)

**Configuración:**
- Archivo: `config/msalConfig.js`
- Proveedor: Azure Active Directory
- Scope: `User.Read`

**Flujo:**
1. Usuario inicia la app sin autenticarse
2. MSAL detecta falta de sesión
3. Redirige a login de Azure
4. Usuario se autentica
5. Se obtiene token de acceso
6. Se captura email del usuario
7. Email se envía con cada solicitud API para tracking

---

## 🎨 Estilos y Animaciones

- **CSS:** `App.css`, `index.css` - Estilos gráficos
- **Animaciones:** Librería `motion` - Transiciones suaves
- **UI Components:** Ant Design - Componentes preconstruidos
- **Gráficos:** Recharts - Visualizaciones interactivas

---

## 🚀 Scripts Disponibles

```bash
# Desarrollo (Vite dev server con HMR)
npm run dev

# Build para producción
npm run build

# Linting (validar código)
npm run lint

# Preview de build
npm run preview
```

---

## 🔗 Integración Backend

El frontend se comunica con un **backend independiente** (típicamente en `http://localhost:8765`):

- **Puerto Backend:** 8765 (configurable vía `VITE_BACKEND_PORT`)
- **Versión API:** v1
- **Respuestas:** JSON
- **Streaming:** Soportado para síntesis y chat en tiempo real

---

## 📊 Flujo de Datos

```
Usuario
  ↓
[Interfaz UI] (React Components)
  ↓
[api.js] (Cliente HTTP)
  ↓
[Backend API] (Python/FastAPI)
  ↓
[Base de datos + LLM]
  ↓
[Respuesta al usuario]
```

---

## ⚙️ Variables de Entorno

Configurables en `.env` o variables del navegador:
```
VITE_BACKEND_HOST    # Host del backend (default: localhost)
VITE_BACKEND_PORT    # Puerto del backend (default: 8765)
VITE_BACKEND_URL_V1  # URL completa backend v1
```

---

## 🚢 Deploy

- **Docker:** Se proporciona `dockerfile` para containerizar
- **Azure:** Script `deploy_acr.sh` para desplegar en Azure Container Registry
- **Build:** `npm run build` genera carpeta `dist/` lista para servir

---

## 📝 Notas Importantes

1. **Token de MSAL:** Se obtiene silenciosamente. Si expira, se pide re-autenticación
2. **Email del usuario:** Capturado y enviado con cada solicitud para análisis
3. **Feedback:** Sistema de estrellas + comentarios para mejorar la IA
4. **Streaming:** Síntesis y chat usan streaming para respuestas en tiempo real
5. **PDF:** Integrado directamente en el chatbot para visualización rápida

---

## 🎓 Resumen Ejecutivo

**Memorias 975** es una plataforma de **IA y búsqueda inteligente** para información jurídica colombiana. Combina:
- **Chat conversacional** con IA
- **Búsqueda semántica** avanzada
- **Visualización de grafos** de relaciones
- **Síntesis automática** de documentos
- **Sistema de feedback** para mejora continua
- **Panel de control** con métricas de uso

Todo integrado en una experiencia web moderna con React, autenticación segura con Azure, y comunicación fluida con un backend inteligente.

---

**Última actualización:** 2026-02-26  
**Versión Frontend:** 0.0.0  
**Tecnología:** React 19 + Vite 6 + Ant Design 5
