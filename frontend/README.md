# Proyecto Memorias 975 - Frontend

## Estructura
- `src/` - Código fuente React
- `public/` - Archivos estáticos
- `package.json` - Dependencias y scripts

## Requisitos
- Node.js 18+
- npm

## Instalación

1. Instala las dependencias:
   ```bash
   npm install
   ```

## Ejecución

### Solo frontend
```bash
npm run dev
```
Esto levanta la app en http://localhost:5173

### Backend
El backend debe estar corriendo en http://localhost:5555 (ver carpeta `../backend/`).

---

## Notas
- Si cambias la URL del backend, actualízala en `src/api.js`.
- Para producción, usa `npm run build` y sirve la carpeta `dist/`.
