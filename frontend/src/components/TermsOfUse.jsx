import React from "react";

export default function TermsOfUse({ onAccept }) {
  return (
    <div style={{ maxWidth: 700, margin: "40px auto", padding: 32, background: "#fff", borderRadius: 12, boxShadow: "0 2px 12px rgba(0,0,0,0.08)" }}>
      <h2>Términos de Uso y Consideraciones sobre el Uso Responsable de la IA</h2>
      <p>
        Bienvenido a <b>Memorias de Justicia y Paz</b>. Antes de utilizar la aplicación, es importante que leas y aceptes los siguientes términos:
      </p>
      <ul>
        <li><b>Elasticsearch:</b> Los resultados dependen de la calidad y estructura de los datos indexados.</li>
        <li><b>Modelos LLM:</b> Los resúmenes y análisis generados por IA no sustituyen el juicio profesional ni constituyen asesoría legal.</li>
        <li><b>Visualización de grafos:</b> Las relaciones mostradas son aproximaciones basadas en algoritmos y datos disponibles.</li>
        <li><b>Educación y transparencia:</b> Comprender las limitaciones de la IA te permitirá usar la herramienta de manera más efectiva y responsable.</li>
      </ul>
      <p>
        <b>Al aceptar, reconoces haber leído y entendido estas consideraciones y aceptas utilizar la herramienta como un apoyo orientativo.</b>
      </p>
      <p style={{ color: "#b00", fontWeight: 500 }}>
        <b>Nota:</b> Esta aplicación no garantiza resultados concluyentes ni reemplaza el asesoramiento profesional.
      </p>
      <button onClick={onAccept} style={{ marginTop: 24, padding: "10px 32px", fontSize: 18, background: "#4ECDC4", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer" }}>
        Acepto y Comprendo
      </button>
    </div>
  );
}
