import React, { useEffect, useState } from "react";
import ChatTab from "./components/ChatTab";
import SimpleSearchTab from "./components/SimpleSearchTab";
import SherlockTab from "./components/SherlockTab";
import AboutTab from "./components/AboutTab";
import DashboardTab from "./components/DashboardTab";
import TermsOfUse from "./components/TermsOfUse";
import EmailPrompt from "./components/EmailPrompt";
import "./App.css";
import {
  AuthenticatedTemplate,
  UnauthenticatedTemplate,
  useMsal,
} from "@azure/msal-react";
import { fetchData } from "./api";

export default function App() {
  const [userEmail, setUserEmail] = useState("");
  const { instance, accounts } = useMsal();

  const [tab, setTab] = useState("chat");

  // Estado global para búsqueda avanzada
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [graph, setGraph] = useState(null);
  const [synthesis, setSynthesis] = useState("");
  const [idFeedback, setIdFeedback] = useState("");
  const [modelSearch, setModelSearch] = useState("");
  const [sortedResults, setSortedResults] = useState([]);
  const [currentChunkIndex, setCurrentChunkIndex] = useState(null);
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hola, soy el chatbot creado para suministrar información sobre las sentencias de la ley 975, ¿en qué puedo ayudarte hoy?",
      sender: "bot",
    },
  ]);
  const [message, setMessage] = useState("");
  const [selectedValue, setSelectedValue] = useState("");

  const handleEmailSubmit = (email) => {
    setUserEmail(email);
    sessionStorage.setItem("userEmail", email);
  };

  useEffect(() => {
    if (accounts.length <= 0) return;
    const request = {
      scopes: ["User.Read"],
      account: accounts[0],
    };

    instance
      .acquireTokenSilent(request)
      .then((response) => {
        const accessToken = response.accessToken;

        // Llamar a Microsoft Graph API
        return fetch("https://graph.microsoft.com/v1.0/me", {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
      })
      .then((res) => res.json())
      .then((data) => {
        handleEmailSubmit(data.mail || data.username);
      })
      .catch((error) => {
        console.error("Error al obtener datos del usuario:", error);
      });
  }, [accounts, instance]);

  const inSignOut = () => {
    instance.logoutPopup({
      postLogoutRedirectUri: "/",
    });
  };

  const [access, setAccess] = useState(null);
  const [isLoadingAccess, setIsLoadingAccess] = useState(true);
  function fetchInfoUser() {
    if (userEmail) {
      setAccess(true);
      fetchData({
        url: "/users_auth/users_auth",
        method: "POST",
        body: { e_mail: userEmail },
      })
        .then((res) => {
          setAccess(res.access);
        })
        .catch(() => setAccess(null))
        .finally(() => setIsLoadingAccess(false));
    } else {
      setAccess(null);
    }
  }

  useEffect(() => {
    fetchInfoUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userEmail]);

  return (
    <>
      <UnauthenticatedTemplate>
        <EmailPrompt onEmailSubmit={handleEmailSubmit} />
      </UnauthenticatedTemplate>
      <AuthenticatedTemplate>
        {isLoadingAccess ? (
          <p>Cargando...</p>
        ) : (
          <>
            {access != null ? (
              <div
                style={{
                  maxWidth: tab === "chat" ? "none" : 1200,
                  margin: "0 auto",
                  padding: tab === "chat" ? 0 : 24,
                }}
              >
                <h1 style={{ textAlign: "center", marginBottom: 24 }}>
                  Memorias de Justicia y Paz
                </h1>
                <div
                  style={{
                    textAlign: "right",
                    marginBottom: "1rem",
                    display: "flex",
                    justifyContent: "flex-end",
                    gap: "1rem",
                  }}
                >
                  <span style={{ fontStyle: "italic" }}>{userEmail}</span>
                  <button onClick={() => inSignOut()}>Cerrar sesión</button>
                </div>
                <nav className="tab-nav">
                  <button
                    className={`tab-btn${tab === "chat" ? " active" : ""}`}
                    onClick={() => setTab("chat")}
                  >
                    Chat
                  </button>
                  {/* <button
          className={`tab-btn${tab === "sherlock" ? " active" : ""}`}
          onClick={() => setTab("sherlock")}
        >
          Pregúntale a Sherlock
        </button> */}
                  <button
                    className={`tab-btn${tab === "search" ? " active" : ""}`}
                    onClick={() => setTab("search")}
                  >
                    Búsqueda Avanzada
                  </button>
                  <button
                    className={`tab-btn${tab === "about" ? " active" : ""}`}
                    onClick={() => setTab("about")}
                  >
                    Acerca de
                  </button>
                  <button
                    className={`tab-btn${tab === "dashboard" ? " active" : ""}`}
                    onClick={() => setTab("dashboard")}
                  >
                    Indicadores de uso
                  </button>
                </nav>
                {tab === "chat" && (
                  <ChatTab
                    access={access}
                    messages={messages}
                    setMessages={setMessages}
                    message={message}
                    setMessage={setMessage}
                    selectedValue={selectedValue}
                    setSelectedValue={setSelectedValue}
                  />
                )}
                {/* {tab === "sherlock" && <SherlockTab userEmail={userEmail} />} */}
                {tab === "search" && (
                  <SimpleSearchTab
                    query={query}
                    setQuery={setQuery}
                    results={results}
                    setResults={setResults}
                    graph={graph}
                    setGraph={setGraph}
                    synthesis={synthesis}
                    setSynthesis={setSynthesis}
                    setIdFeedback={setIdFeedback}
                    idFeedback={idFeedback}
                    modelSearch={modelSearch}
                    setModelSearch={setModelSearch}
                    setSortedResults={setSortedResults}
                    sortedResults={sortedResults}
                    setCurrentChunkIndex={setCurrentChunkIndex}
                    currentChunkIndex={currentChunkIndex}
                  />
                )}
                {tab === "about" && <AboutTab />}
                {tab === "dashboard" && <DashboardTab />}
                {/* Placeholder para futuras condiciones o props en Indicadores de uso */}
              </div>
            ) : (
              <div
                style={{
                  height: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexDirection: "column",
                  textAlign: "center",
                  padding: "20px",
                }}
              >
                <h2>Acceso restringido</h2>
                <p style={{ maxWidth: 400, padding: 0, margin: 0 }}>
                  No tienes permisos para ver este módulo. Si crees que esto es
                  un error, por favor contacta al administrador.
                </p>
                <button style={{marginTop:"12px"}} onClick={() => inSignOut()}>Cerrar sesión</button>
              </div>
            )}
          </>
        )}
      </AuthenticatedTemplate>
    </>
  );
}
