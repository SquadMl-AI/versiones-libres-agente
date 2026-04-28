import React from "react";

export default function AboutTab() {
  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '2em 1em', textAlign: 'left', fontSize: '1.08em', lineHeight: 1.7 }}>
      <h2 style={{ color: '#1a237e', marginBottom: 8 }}>Acerca de la Aplicación</h2>

      <section style={{ marginBottom: 24 }}>
        <p>
          <b>Esta herramienta está diseñada para facilitar la exploración, búsqueda y análisis de documentos jurídicos relacionados con la Ley 975 (Justicia y Paz), utilizando inteligencia artificial para agilizar el trabajo de los funcionarios de la Fiscalía General de la Nación.</b>
        </p>
        <div style={{ background: '#fffbe6', border: '1px solid #ffe082', borderRadius: 8, padding: '1em 1.2em', margin: '1em 0', color: '#b22222' }}>
          <b>Importante:</b> Los resultados y resúmenes generados por IA <b>deben ser revisados y validados por profesionales</b> antes de ser usados en procesos judiciales o decisiones institucionales. <br />Esta herramienta es un apoyo orientativo y <b>no reemplaza el análisis humano ni constituye prueba judicial</b>.
        </div>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h3 style={{ color: '#1565c0', marginTop: 0 }}>Principales funcionalidades</h3>
        <ul style={{ paddingLeft: 22 }}>
          <li><b>Búsqueda por colección:</b> Filtra tu búsqueda seleccionando una o varias colecciones temáticas de documentos.</li>
          <li><b>Resultados priorizados por IA:</b> Recupera los fragmentos más relevantes usando modelos de lenguaje y técnicas híbridas.</li>
          <li><b>Síntesis automática:</b> Solicita un resumen generado por IA de los hallazgos más importantes.</li>
          <li><b>Exploración visual:</b> Visualiza conexiones y relaciones entre colecciones, documentos y fragmentos relevantes mediante un grafo interactivo.</li>
          <li><b>Transparencia y trazabilidad:</b> Cada resultado muestra su colección y contexto para facilitar la auditoría y validación.</li>
          <li><b>Indicadores de uso:</b> Consulta métricas de uso y feedback para monitorear el impacto y la calidad de las búsquedas.</li>
        </ul>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h3 style={{ color: '#1565c0' }}>¿Cómo funciona?</h3>
        <ol style={{ paddingLeft: 22 }}>
          <li><b>Escribe tu consulta:</b> Ingresa una pregunta o palabras clave y selecciona las colecciones de interés.</li>
          <li><b>Búsqueda inteligente:</b> El sistema prioriza los fragmentos más relevantes usando IA.</li>
          <li><b>Clasificación de relevancia:</b> Los fragmentos se clasifican como <b>Relevante</b>, <b>Indeterminada</b> o <b>No relevante</b> respecto a tu consulta.</li>
          <li><b>Visualización y síntesis:</b> Explora los resultados, visualiza relaciones y solicita un resumen automático.</li>
          <li><b>Auditoría y validación:</b> Consulta la colección y el contexto de cada fragmento recuperado.</li>
        </ol>
      </section>

      <section style={{ marginBottom: 28 }}>
        <h3 style={{ color: '#1565c0' }}>Recomendaciones de uso</h3>
        <ul style={{ paddingLeft: 22 }}>
          <li><b>Uso responsable:</b> La herramienta es un apoyo, pero no reemplaza el análisis profesional ni la revisión experta.</li>
          <li><b>Privacidad y ética:</b> Utiliza la aplicación respetando la confidencialidad y los principios éticos institucionales.</li>
          <li><b>Consulta al equipo:</b> Si tienes dudas técnicas o necesitas ayuda, contacta al equipo de desarrollo o consulta la documentación.</li>
        </ul>
      </section>

      <section style={{ marginBottom: 18 }}>
        <h3 style={{ color: '#1565c0' }}>Créditos y contacto</h3>
        <ul style={{ paddingLeft: 22 }}>
          <li><b>Desarrollo:</b> Equipo IA Fiscalía General de la Nación</li>
          <li><b>Contacto técnico:</b> <a href="mailto:soporte-ia@fiscalia.gov.co">soporte-ia@fiscalia.gov.co</a></li>
          <li><b>Repositorio:</b> <a href="https://github.com/aifiscalia/sentencias_975_react" target="_blank" rel="noopener noreferrer">GitHub - sentencias_975_react</a></li>
        </ul>
      </section>

      <div style={{ marginTop: '2em', fontStyle: 'italic', color: '#616161', fontSize: '0.98em' }}>
        Para más detalles técnicos o soporte, por favor contacta al equipo de desarrollo.<br />
        Última actualización: julio 2025
      </div>
    </div>
  );
}
