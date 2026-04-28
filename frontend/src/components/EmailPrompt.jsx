import { useMsal } from "@azure/msal-react";
import { useState } from "react";

export default function EmailPrompt({ onEmailSubmit }) {
  const { instance } = useMsal();
  const [error] = useState("");
  const [accepted, setAccepted] = useState(false);
  const [termsOpen, setTermsOpen] = useState(false);

  const manageMicrosoftAccount = (account) => {
    onEmailSubmit(account.username);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    instance.loginPopup().then((res) => {
      // Handle successful login
      manageMicrosoftAccount(res.account);
    });
  };

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          padding: "2rem",
          border: "1px solid #ccc",
          borderRadius: "8px",
          boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
        }}
      >
        <h2>Identificación de Funcionario</h2>
        <div
          style={{
            background: "#f8f8f8",
            border: "1px solid #eee",
            borderRadius: 6,
            padding: "1rem",
            marginBottom: "1rem",
            fontSize: 14,
          }}
        >
          <b>AVISO IMPORTANTE:</b> Al ingresar su correo institucional y
          continuar, usted acepta los términos y condiciones de uso de esta
          plataforma, incluyendo el tratamiento de datos y la política de
          privacidad institucional.
          <details
            style={{ marginTop: 10 }}
            open={termsOpen}
            onToggle={(e) => setTermsOpen(e.target.open)}
          >
            <summary
              style={{
                cursor: "pointer",
                color: "#007bff",
                fontWeight: 500,
                outline: "none",
              }}
            >
              Ver términos y condiciones
            </summary>
            <div
              style={{
                marginTop: 10,
                maxHeight: 200,
                overflowY: "auto",
                fontSize: 13,
                paddingRight: 8,
                textAlign: "justify",
              }}
            >
              <b>Términos y Condiciones de Uso</b>
              <ol>
                <li>
                  <b>Finalidad y Alcance</b>
                  <br />
                  Esta plataforma está diseñada como una herramienta de apoyo
                  orientativo para funcionarios de la Fiscalía General de la
                  Nación, facilitando la exploración, análisis y síntesis de
                  información jurídica y documental relacionada con la Ley 975
                  (Justicia y Paz) en Colombia. Su objetivo es agilizar la
                  búsqueda y el análisis de grandes volúmenes de documentos,
                  pero{" "}
                  <b>
                    no reemplaza el análisis humano ni constituye prueba
                    judicial
                  </b>
                  .
                </li>
                <li>
                  <b>Uso Responsable y Ético</b>
                  <br />
                  El usuario se compromete a utilizar la herramienta de manera
                  complementaria a su labor profesional, respetando la
                  confidencialidad, la protección de datos y los principios
                  éticos institucionales. Los resultados generados por la
                  plataforma deben ser interpretados y validados por
                  profesionales expertos antes de ser utilizados en procesos
                  judiciales, administrativos o de toma de decisiones
                  institucionales.
                </li>
                <li>
                  <b>Limitaciones de la Inteligencia Artificial</b>
                  <br />
                  Los resúmenes, análisis y clasificaciones generados por
                  modelos de lenguaje (IA){" "}
                  <b>
                    no sustituyen el juicio profesional ni constituyen asesoría
                    legal
                  </b>
                  . La información presentada es orientativa y puede contener
                  errores, omisiones o interpretaciones automáticas que deben
                  ser revisadas por el usuario.
                </li>
                <li>
                  <b>Limitaciones Técnicas de la Herramienta</b>
                  <br />
                  Los resultados dependen de la calidad y estructura de los
                  datos indexados en Elasticsearch y de la correcta
                  configuración de los modelos de IA. Las visualizaciones de
                  grafos y relaciones son aproximaciones basadas en algoritmos y
                  datos disponibles, y no deben considerarse como
                  representaciones exhaustivas o definitivas. La plataforma
                  puede experimentar limitaciones técnicas, demoras o
                  interrupciones en el servicio debido a la dependencia de
                  servicios externos de IA y búsqueda.
                </li>
                <li>
                  <b>Transparencia y Trazabilidad</b>
                  <br />
                  Cada resultado muestra su origen, colección y contexto,
                  permitiendo auditoría y validación por parte del usuario. El
                  sistema traduce automáticamente los identificadores técnicos a
                  nombres legibles para facilitar la navegación y el filtrado.
                </li>
                <li>
                  <b>Aceptación de los Términos</b>
                  <br />
                  Al ingresar su correo institucional y utilizar la plataforma,
                  el usuario declara haber leído, entendido y aceptado estos
                  términos y condiciones, reconociendo los límites y el carácter
                  orientativo de la herramienta.
                </li>
              </ol>
              <p style={{ color: "#b00", fontWeight: 500 }}>
                <b>Nota:</b> Esta aplicación no garantiza resultados
                concluyentes ni reemplaza el asesoramiento profesional. El uso
                de la información generada es responsabilidad exclusiva del
                usuario.
              </p>
            </div>
          </details>
        </div>
        {/* <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="su.correo@fiscalia.gov.co"
          style={{ width: "100%", padding: "0.5rem", marginBottom: "1rem" }}
        /> */}
        <div style={{ marginBottom: "1rem", fontSize: 13 }}>
          <label>
            <input
              type="checkbox"
              checked={accepted}
              onChange={(e) => setAccepted(e.target.checked)}
              style={{ marginRight: 8 }}
              disabled={!termsOpen}
            />
            Acepto los términos y condiciones de uso
          </label>
        </div>
        {error && <p style={{ color: "red" }}>{error}</p>}
        <button
          type="submit"
          style={{
            width: "100%",
            padding: "0.75rem",
            backgroundColor: "#111",
            color: "white",
            border: "2px solid black",
            borderRadius: "4px",
          }}
          disabled={!accepted}
        >
          Ingresar con Microsoft
        </button>
      </form>
    </div>
  );
}
