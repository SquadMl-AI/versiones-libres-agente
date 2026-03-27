import React, { useState, useEffect } from "react";
import StarRating from "./StarRating";
import ReactMarkdown from "react-markdown";
import { fetchData } from "../api";
import VisNetworkGraph from "./VisNetworkGraph";

// Lista de "stop words" en español a ignorar en el resaltado

export default function SimpleSearchTab({
  query,
  setQuery,
  setGraph,
  synthesis,
  setSynthesis,
  setIdFeedback,
  idFeedback,
  sortedResults,
  setSortedResults,
  setCurrentChunkIndex,
  currentChunkIndex,
}) {
  const [loadingSynthesis, setLoadingSynthesis] = useState(false);
  const [relevanceCategories, setRelevanceCategories] = useState(["Relevante"]);
  const [selectedChunks, setSelectedChunks] = useState([]);
  const [loadingRelevance, setLoadingRelevance] = useState(false);
  const [progressRelevance, setProgressRelevance] = useState({
    current: 0,
    total: 0,
  });
  const [selectedCollections, setSelectedCollections] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  // Feedback con estrellas para grafo
  const [graphRating, setGraphRating] = useState(0);
  const [graphComment, setGraphComment] = useState("");
  const [graphFeedbackSent, setGraphFeedbackSent] = useState(false);
  // Feedback con estrellas para síntesis
  const [synthesisRating, setSynthesisRating] = useState(0);
  const [synthesisComment, setSynthesisComment] = useState("");
  const [synthesisFeedbackSent, setSynthesisFeedbackSent] = useState(false);

  const [isButtonHovered, setIsButtonHovered] = useState(false);
  const [isFiltersVisible, setIsFiltersVisible] = useState(false);
  const [isSynthesisVisible, setIsSynthesisVisible] = useState(true);

  // Estado para collections
  const [collections, setCollections] = useState([]);
  const relevanceOptions = [
    "Relevante",
    "Relevancia Indeterminada",
    "No Relevante",
  ];

  // (Eliminado: estados duplicados de feedback)
  useEffect(() => {
    if (selectedCollections.length > 0) {
      // Obtener documentos de todas las colecciones seleccionadas
      const fetchDocuments = async () => {
        fetchData({
          url: `/files/list_files/`,
          method: "GET",
          params: {
            bloque:
              selectedCollections[0] == "all"
                ? collections
                : selectedCollections,
          },
        }).then((res) => {
          setDocuments(res);
        });
      };
      fetchDocuments();
    } else {
      setDocuments([]);
      setSelectedDocuments([]);
    }
  }, [selectedCollections, collections]); // Corregido: añadida dependencia 'collections'

  // Construir lista de colecciones a partir del JSON
  // const collections = [
  //   { id: "", name: "Todas las colecciones" },
  //   ...Object.entries(collectionsMap).map(([id, name]) => ({ id, name })),
  // ];

  function chunksArrayToTree(chunksArray) {
    const folderMap = {};
    const usedDocIds = new Set(); // Trackea documentos ya agregados
    const usedChunkIds = new Set(); // Trackea chunks únicos

    chunksArray.forEach((chunk) => {
      const folder = chunk.folder;
      const document = chunk.document_name;

      if (!folderMap[folder]) folderMap[folder] = {};
      if (!folderMap[folder][document]) folderMap[folder][document] = [];

      folderMap[folder][document].push(chunk);
    });

    // 2. Construir el árbol
    const root = {
      id: "root",
      children: Object.entries(folderMap).map(([folder, docs]) => ({
        id: folder,
        children: Object.entries(docs).map(([doc, chunkArr]) => {
          // Crear un ID único para el documento si está duplicado
          let docId = doc;
          while (usedDocIds.has(docId)) {
            docId = `${doc}_${Math.random().toString(36).substr(2, 4)}`;
          }
          usedDocIds.add(docId);

          const uniqueChunks = [];
          chunkArr.forEach((chunk) => {
            let chunkId = chunk["chunk id"];
            while (usedChunkIds.has(chunkId)) {
              chunkId = `${chunk["chunk id"]}_${Math.random()
                .toString(36)
                .substr(2, 4)}`;
            }
            usedChunkIds.add(chunkId);

            uniqueChunks.push({
              id: chunkId,
              ...chunk,
            });
          });

          return {
            id: docId,
            children: uniqueChunks,
          };
        }),
      })),
    };

    return root;
  }

  const [threeData, setThreeData] = useState(null);

  function postFeedback(chunks, email, model) {
    const data = {
      user_email: email,
      query,
      model,
      results: chunks.map((chunk) => {
        return chunk?.resumen_llm ?? "";
      }),
      stars_graph: 0,
      feed_graph: "",
      stars_synthe: 0,
      feed_synthe: "",
      synthesis: "",
    };
    fetchData({ url: "/feedbacks", body: data, method: "POST" }).then((res) => {
      setIdFeedback(res.feedback_id);
    });
  }

  const handleSearch = () => {
    setIdFeedback("");
    setLoadingRelevance(true);
    setProgressRelevance({ current: 0, total: 0 });
    setGraph(null);
    setSynthesis("");
    // Limpiar feedback de estrellas
    setGraphRating(0);
    setGraphComment("");
    setGraphFeedbackSent(false);
    setSynthesisRating(0);
    setSynthesisComment("");
    setSynthesisFeedbackSent(false);
    setSelectedChunks([]);
    setThreeData(null);
    const userEmail = sessionStorage.getItem("userEmail");
    fetchData({
      url: `/advance_search/advance_search`,
      method: "POST",
      body: {
        query,
        bloque:
          selectedCollections[0] == "all" ? collections : selectedCollections,
        file: selectedDocuments,
        user_id: userEmail,
      },
    })
      .then((res) => {
        const chunksArray = [
          ...res.high_score_categorized_chunks,
          ...res.low_score_reranked_chunks,
          ...res.remaining_chunks,
        ];
        postFeedback(chunksArray, userEmail, res.model);
        setSortedResults(chunksArray);
        setCurrentChunkIndex(0);
        setLoadingRelevance(false);
        setProgressRelevance({ current: 0, total: 0 });
      })
      .catch((error) => {
        console.error("Error al realizar la búsqueda:", error);
        setLoadingRelevance(false);
        setProgressRelevance({ current: 0, total: 0 });
      });

    // Facetas dinámicas: renderizado y lógica de selección
    // Declarar la función fuera de cualquier otro bloque para evitar ReferenceError
  };

  useEffect(() => {
    if (sortedResults.length > 0) {
      const three = chunksArrayToTree(sortedResults);
      setThreeData(three);
    }
  }, [sortedResults]);

  const handleSynthesis = () => {
    setLoadingSynthesis(true);
    setSynthesis("");
    const chunks = sortedResults.filter((chunk) =>
      selectedChunks.length > 0
        ? selectedChunks.includes(chunk["chunk id"]) &&
          relevanceCategories.includes(chunk.categoria)
        : relevanceCategories.includes(chunk.categoria)
    );

    fetchData({
      url: "/synthesis_chuks/synthesis_chunks",
      method: "POST",
      body: { query, chunks },
    })
      .then((res) => {
        setSynthesis(res.synthesized_text);
        fetchData({
          url: "/feedbacks/synthe",
          body: {
            feedback_id: idFeedback,
            synthesis: res.synthesized_text,
          },
          method: "PUT",
        });
      })
      .finally(() => {
        setLoadingSynthesis(false);
      });
  };

  const handleChunkToggle = (id) => {
    setSelectedChunks((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };
  // Ordenar los resultados por score descendente para el visor uno a uno
  const [currentChunk, setCurrentChunk] = useState(-1);

  useEffect(() => {
    if (currentChunkIndex >= 0 && sortedResults && sortedResults.length > 0) {
      setCurrentChunk(sortedResults[currentChunkIndex]);
    }
  }, [currentChunkIndex, sortedResults]);

  useEffect(() => {
    fetchData({ url: "/folders/list_folders" }).then((data) => {
      setCollections(data);
    });
  }, []);

  return (
    <div>
      <h2>Búsqueda avanzada de referencias</h2>
      <div style={{ margin: "24px 0", textAlign: "center" }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Escribe tu consulta"
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleSearch();
            }
          }}
          style={{
            width: "60%",
            padding: "12px 20px",
            fontSize: "18px",
            borderRadius: "24px",
            border: "1px solid #ddd",
            marginRight: "12px",
          }}
        />
        <button
          onClick={handleSearch}
          disabled={loadingRelevance}
          style={{
            padding: "12px 24px",
            fontSize: "18px",
            borderRadius: "24px",
            border: "1px solid #ccc",
            background: isButtonHovered ? "#f0f0f0" : "white",
            color: "#333",
            cursor: "pointer",
            transition: "background-color 0.3s ease",
          }}
          onMouseEnter={() => setIsButtonHovered(true)}
          onMouseLeave={() => setIsButtonHovered(false)}
        >
          Buscar
        </button>
      </div>

      <details
        open={isFiltersVisible}
        onToggle={() => setIsFiltersVisible(!isFiltersVisible)}
        style={{
          marginBottom: "24px",
          border: "1px solid #ddd",
          borderRadius: "8px",
          padding: "12px",
        }}
      >
        <summary style={{ cursor: "pointer", fontWeight: "bold" }}>
          {isFiltersVisible ? "Ocultar Filtros" : "Mostrar Filtros"}
        </summary>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "16px",
            marginTop: "12px",
          }}
        >
          {/* Contenedor para los filtros de colección y documento */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "16px",
            }}
          >
            <div>
              <label
                style={{
                  display: "block",
                  marginBottom: 8,
                  color: "#555",
                  fontSize: "14px",
                  textAlign: "center",
                }}
              >
                Colección:
              </label>
              <select
                value={selectedCollections}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === "all") {
                    setSelectedCollections(["all"]);
                  } else {
                    setSelectedCollections((prev) => {
                      if (prev.length === 1 && prev[0] === "all") {
                        return [value];
                      }

                      if (prev.includes(value)) {
                        return prev;
                      }

                      return [...prev, value];
                    });
                  }
                }}
                multiple
                style={{
                  padding: "8px 12px",
                  borderRadius: "8px",
                  border: "1px solid #ccc",
                  background: "white",
                  fontSize: "14px",
                  height: 120,
                  overflowY: "auto",
                  minWidth: "250px",
                }}
              >
                <option value={"all"}>Todas las colecciones</option>
                {collections.map((c, i) => (
                  <option key={i} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            {selectedCollections.length > 0 && documents.length > 0 && (
              <div>
                <label
                  style={{
                    display: "block",
                    marginBottom: 8,
                    color: "#555",
                    fontSize: "14px",
                    textAlign: "center",
                  }}
                >
                  Documento:
                </label>
                <select
                  value={selectedDocuments}
                  onChange={(e) => {
                    const value = e.target.value;

                    if (value === "all") {
                      setSelectedDocuments(documents);
                    } else {
                      setSelectedDocuments((prev) => {
                        if (prev.length === 1 && prev[0] === "all") {
                          return [value];
                        }

                        if (prev.includes(value)) {
                          return prev; // evitar duplicados
                        }

                        return [...prev, value];
                      });
                    }
                  }}
                  multiple
                  style={{
                    padding: "8px 12px",
                    borderRadius: "8px",
                    border: "1px solid #ccc",
                    background: "white",
                    fontSize: "14px",
                    height: 120,
                    overflowY: "auto",
                    minWidth: "250px",
                  }}
                >
                  <option value={"all"}>Todos los documentos</option>
                  {documents.map((doc, i) => (
                    <option key={i} value={doc}>
                      {doc}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
          {/* Contenedor para el input de chunks */}
          {/* <div style={{ marginTop: 12 }}>
            <label style={{ marginRight: 8, color: "#555", fontSize: "14px" }}>
              Chunks a analizar con LLM:
            </label>
            <input
              type="number"
              min={1}
              max={100}
              value={maxLlmChunks}
              onChange={(e) => {
                const value = Number(e.target.value);
                if (value <= 100) {
                  setMaxLlmChunks(value);
                }
              }}
              style={{
                width: 60,
                padding: "8px 12px",
                borderRadius: "8px",
                border: "1px solid #ccc",
                background: "white",
                fontSize: "14px",
              }}
            />
          </div> */}
        </div>
      </details>

      {loadingRelevance && (
        <div style={{ margin: "18px 0" }}>
          <div
            style={{
              height: 8,
              background: "#eee",
              borderRadius: 4,
              overflow: "hidden",
              marginBottom: 6,
            }}
          >
            <div
              className="progress-bar-animated"
              style={{
                width:
                  progressRelevance.total > 0
                    ? `${
                        (progressRelevance.current / progressRelevance.total) *
                        100
                      }%`
                    : "100%",
                height: "100%",
                background: "#4ECDC4",
                transition: "width 0.3s",
              }}
            />
          </div>
          <div style={{ fontSize: 14, color: "#555" }}>
            Analizando relevancia...{" "}
            {progressRelevance.total > 0
              ? `${progressRelevance.current} / ${progressRelevance.total}`
              : ""}
          </div>
        </div>
      )}
      {/* Facetas dinámicas sobre los resultados */}
      {sortedResults?.length > 0 && (
        <div style={{ margin: "24px 0" }}>
          {/* Resumen del análisis de relevancia */}
          <div
            style={{
              margin: "18px 0 0 0",
              padding: "12px",
              background: "#fff",
              border: "1px solid #cce1f7",
              borderRadius: 8,
              fontSize: 15,
            }}
          >
            {(() => {
              const totalChunks = sortedResults.length;
              const analizados = sortedResults.filter(
                (r) => r.categoria && r.categoria !== "No analizado"
              ).length;
              const categorias = sortedResults.reduce((acc, r) => {
                const cat =
                  typeof r.categoria === "string"
                    ? r.categoria
                    : "No Analizado";
                acc[cat] = (acc[cat] || 0) + 1;
                return acc;
              }, {});
              // Construir narración
              let narracion = `De un total de ${totalChunks} fragmentos recuperados de la base de conocimientos, se analizaron con IA los ${analizados} con mayor score de similitud híbrida.`;
              const partes = [];
              if (categorias["Relevante"])
                partes.push(
                  `${categorias["Relevante"]} fueron considerados relevantes`
                );
              if (categorias["Relevancia indeterminada"])
                partes.push(
                  `${categorias["Relevancia indeterminada"]} quedaron como relevancia indeterminada`
                );
              if (categorias["No relevante"])
                partes.push(
                  `${categorias["No relevante"]} se clasificaron como no relevantes`
                );
              if (categorias["No analizado"])
                partes.push(
                  `${categorias["No analizado"]} no fueron analizados por el modelo`
                );
              if (partes.length > 0) {
                narracion +=
                  " De los fragmentos analizados, " +
                  partes.join(", ").replace(/, ([^,]*)$/, " y $1") +
                  ".";
              }
              return (
                <>
                  <b>Balance del análisis preliminar de relevancia:</b>
                  <br />
                  {narracion}
                </>
              );
            })()}
          </div>
          {/* Visor uno a uno de chunks ordenados por score en acordeón colapsable */}
          <details
            open
            style={{
              margin: "24px 0",
              border: "1px solid #ddd",
              borderRadius: 8,
              background: "#fff",
              boxShadow: "0 2px 8px #e0f2e9",
              padding: 0,
            }}
          >
            <summary
              style={{
                cursor: "pointer",
                fontWeight: "bold",
                fontSize: 16,
                padding: 16,
                color: "#333",
                outline: "none",
                fontFamily: "inherit",
              }}
            >
              Detalles de los fragmentos recuperados
            </summary>
            <div style={{ padding: 16 }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: 12,
                }}
              >
                <button
                  onClick={() =>
                    setCurrentChunkIndex((i) => Math.max(0, i - 1))
                  }
                  disabled={currentChunkIndex === 0}
                  style={{
                    padding: "8px 16px",
                    borderRadius: 6,
                    border: "1px solid #ccc",
                    background: currentChunkIndex === 0 ? "#eee" : "#fff",
                    cursor: currentChunkIndex === 0 ? "not-allowed" : "pointer",
                  }}
                >
                  ◀ Anterior
                </button>
                <span style={{ fontWeight: 600, fontSize: 16 }}>
                  Fragmento {currentChunkIndex + 1} de {sortedResults.length}
                </span>
                <button
                  onClick={() =>
                    setCurrentChunkIndex((i) =>
                      Math.min(sortedResults.length - 1, i + 1)
                    )
                  }
                  disabled={currentChunkIndex === sortedResults.length - 1}
                  style={{
                    padding: "8px 16px",
                    borderRadius: 6,
                    border: "1px solid #ccc",
                    background:
                      currentChunkIndex === sortedResults.length - 1
                        ? "#eee"
                        : "#fff",
                    cursor:
                      currentChunkIndex === sortedResults.length - 1
                        ? "not-allowed"
                        : "pointer",
                  }}
                >
                  Siguiente ▶
                </button>
              </div>
              {currentChunk && (
                <div
                  key={currentChunk.id}
                  style={{
                    border: "1px solid #ddd",
                    borderRadius: 8,
                    background: selectedChunks.includes(
                      currentChunk["chunk id"]
                    )
                      ? "#e6f7ff"
                      : "#fff",
                    boxShadow: "0 1px 4px #eee",
                    marginBottom: 0,
                  }}
                >
                  <div
                    style={{
                      fontWeight: 600,
                      fontSize: 16,
                      padding: 8,
                      borderBottom: "1px solid #eee",
                      background: "#f6faf6",
                      display: "flex",
                      alignItems: "center",
                      flexWrap: "wrap",
                      gap: 8,
                    }}
                  >
                    <span style={{ fontWeight: 700 }}>
                      {currentChunk.title || `Chunk ${currentChunkIndex + 1}`}
                    </span>
                    {currentChunk.folder && (
                      <span style={{ color: "#145a32" }}>
                        • [{currentChunk.folder}]
                      </span>
                    )}
                    {currentChunk.document_name && (
                      <span style={{ color: "#333" }}>
                        • {currentChunk.document_name}
                      </span>
                    )}
                    {/* Página: mostrar solo la primera si hay varias */}
                    {currentChunk.page_numbers && (
                      <span style={{ color: "#333" }}>
                        • pág. {currentChunk.page_numbers[0]}
                      </span>
                    )}
                    {currentChunk.reranker_score >= 0 && (
                      <span
                        style={{
                          marginLeft: 8,
                          color: "#888",
                          fontWeight: 400,
                        }}
                      >
                        • SemanticRanking Score:{" "}
                        {Number(currentChunk.reranker_score).toFixed(4)}
                      </span>
                    )}
                    {currentChunk.hybrid_score >= 0 && (
                      <span
                        style={{
                          marginLeft: 8,
                          color: "#888",
                          fontWeight: 400,
                        }}
                      >
                        • Hybrid Score:{" "}
                        {Number(currentChunk.hybrid_score).toFixed(4)}
                      </span>
                    )}
                  </div>
                  <div style={{ padding: 12 }}>
                    <label
                      style={{
                        display: "flex",
                        alignItems: "flex-start",
                        cursor: "pointer",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={selectedChunks.includes(
                          currentChunk["chunk id"]
                        )}
                        onChange={() => {
                          handleChunkToggle(currentChunk["chunk id"]);
                        }}
                        style={{ marginRight: 12, marginTop: 4 }}
                      />
                      <div style={{ flex: 1 }}>
                        <div style={{ marginTop: 6 }}>
                          <div
                            style={{ marginBottom: 4 }}
                            dangerouslySetInnerHTML={{
                              __html: currentChunk.content_highlighted,
                            }}
                          />
                        </div>

                        {currentChunk.resumen_llm && (
                          <div
                            style={{
                              marginTop: 8,
                              background: "#f6f6f6",
                              padding: 8,
                              borderRadius: 6,
                            }}
                          >
                            <b>Resumen LLM:</b>
                            <div
                              style={{ whiteSpace: "pre-wrap", fontSize: 14 }}
                            >
                              {currentChunk.resumen_llm}
                            </div>
                          </div>
                        )}
                        <p>Fuente citada:</p>
                        <ul className="centered-list">
                          <li>Colección: {currentChunk?.folder}</li>
                          <li>Documentos: {currentChunk?.document_name}</li>
                          {currentChunk?.page_numbers && (
                            <li>
                              Página: {currentChunk.page_numbers.join(", ")}{" "}
                            </li>
                          )}
                          <li>Chunk ID: {currentChunk?.["chunk id"]}</li>
                        </ul>
                        <div style={{ marginTop: 8 }}>
                          <b>Relevancia:</b>
                          <select
                            value={currentChunk.categoria}
                            onChange={(e) => {
                              setSortedResults(
                                sortedResults.map((item) =>
                                  item["chunk id"] == currentChunk?.["chunk id"]
                                    ? {
                                        ...item,
                                        categoria: e.target.value,
                                      }
                                    : item
                                )
                              );
                            }}
                            style={{ marginLeft: 8 }}
                          >
                            <option value="Relevante">Relevante</option>
                            <option value="Relevancia Indeterminada">
                              Relevancia Indeterminada
                            </option>
                            <option value="No Relevante">No Relevante</option>
                          </select>
                        </div>
                      </div>
                    </label>
                  </div>
                </div>
              )}
            </div>
          </details>
          {threeData && (
            <div
              style={{
                margin: "24px 0",
                padding: 16,
                border: "1px solid #ddd",
                borderRadius: 8,
              }}
            >
              <VisNetworkGraph threeData={threeData} />

              <div style={{ marginTop: 24, textAlign: "right" }}>
                <span>¿Cómo calificarías la relevancia del grafo?</span>
                <StarRating
                  rating={graphRating}
                  setRating={setGraphRating}
                  disabled={graphFeedbackSent}
                />
                {graphRating > 0 && graphRating <= 3 && !graphFeedbackSent && (
                  <div style={{ marginTop: 8 }}>
                    <textarea
                      value={graphComment}
                      onChange={(e) => setGraphComment(e.target.value)}
                      placeholder="Ayúdanos a mejorar: ¿qué encontraste insatisfactorio en la experiencia? (comentario obligatorio)"
                      rows={2}
                      style={{
                        width: "100%",
                        borderRadius: 6,
                        border: "1px solid #ccc",
                        padding: 8,
                        marginBottom: 8,
                      }}
                    />
                  </div>
                )}
              </div>
              <div style={{ marginTop: 32, textAlign: "right" }}>
                <button
                  onClick={async () => {
                    // Validación: si alguno de los ratings es <=3, comentario obligatorio
                    if (
                      graphRating > 0 &&
                      graphRating <= 3 &&
                      (!graphComment || graphComment.trim() === "")
                    ) {
                      alert(
                        "Por favor, deja un comentario si tu calificación es de 3 estrellas o menos en alguno de los bloques."
                      );
                      return;
                    }

                    const payload = {
                      // Identificación y sesión
                      feedback_id: idFeedback,
                      stars_graph: graphRating,
                      feed_graph: graphRating <= 3 ? graphComment : "",
                    };
                    fetchData({
                      url: "/feedbacks/graph",
                      method: "PUT",
                      body: payload,
                    })
                      .catch(() => {
                        alert("Error al enviar feedback");
                      })
                      .then(() => {
                        setGraphFeedbackSent(true);
                      });
                  }}
                  disabled={graphFeedbackSent || graphRating === 0}
                  style={{
                    background: "#009688",
                    color: "white",
                    border: "none",
                    borderRadius: 4,
                    padding: "8px 24px",
                    cursor: graphFeedbackSent ? "not-allowed" : "pointer",
                    marginLeft: 12,
                    fontSize: 16,
                  }}
                >
                  {graphFeedbackSent
                    ? "¡Gracias por tu feedback!"
                    : "Enviar feedback"}
                </button>
              </div>
            </div>
          )}
          {/* --- BLOQUE DE SÍNTESIS SOLO DESPUÉS DE LA BÚSQUEDA --- */}
          <div
            style={{
              marginTop: 32,
              paddingTop: 24,
              borderTop: "1px solid #eee",
            }}
          >
            <div style={{ marginBottom: 12 }}>
              <label style={{ marginRight: 8 }}>
                Categorías de relevancia para la síntesis:
              </label>
              <select
                multiple
                value={relevanceCategories}
                onChange={(e) => {
                  const selected = Array.from(
                    e.target.selectedOptions,
                    (opt) => opt.value
                  );
                  setRelevanceCategories(selected);
                }}
                style={{ minWidth: 220, minHeight: 60 }}
              >
                {relevanceOptions.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={() => {
                // Forzar el modelo por defecto si está vacío
                handleSynthesis();
              }}
              disabled={loadingSynthesis}
            >
              {loadingSynthesis
                ? "Generando síntesis..."
                : "Generar Síntesis Final "}
            </button>

            {loadingSynthesis && (
              <div style={{ marginTop: 16 }}>
                <div
                  style={{
                    height: 8,
                    background: "#eee",
                    borderRadius: 4,
                    overflow: "hidden",
                  }}
                >
                  <div
                    className="progress-bar-animated"
                    style={{
                      width: "100%",
                      height: "100%",
                      background: "#4ECDC4",
                      animation: "progressBar 1.2s linear infinite",
                    }}
                  />
                </div>
                <div style={{ fontSize: 14, color: "#555", marginTop: 6 }}>
                  Generando síntesis, por favor espera...
                </div>
              </div>
            )}
            {/* SÍNTESIS FINAL EN ACORDEÓN (STREAMING) */}
            <div style={{ marginTop: 16 }}>
              <details
                open={isSynthesisVisible}
                onToggle={(e) => setIsSynthesisVisible(e.target.open)}
                style={{ background: "#f8f8f8", borderRadius: 8, padding: 0 }}
              >
                <summary
                  style={{
                    cursor: "pointer",
                    fontWeight: 600,
                    fontSize: 18,
                    padding: 16,
                    outline: "none",
                  }}
                >
                  Síntesis Final
                  {loadingSynthesis && (
                    <span
                      style={{ marginLeft: 12, fontSize: 14, color: "#888" }}
                    >
                      (generando...)
                    </span>
                  )}
                </summary>
                <div
                  style={{
                    padding: "16px",
                    borderTop: "1px solid #eee",
                    textAlign: "justify",
                    fontSize: "1.1em",
                  }}
                >
                  {synthesis || loadingSynthesis ? (
                    <ReactMarkdown>{synthesis}</ReactMarkdown>
                  ) : (
                    <span style={{ color: "#888" }}>
                      No se ha generado síntesis aún.
                    </span>
                  )}
                  {(synthesis || loadingSynthesis) && (
                    <div style={{ marginTop: 12, textAlign: "right" }}>
                      <span>¿Cómo calificarías esta síntesis?</span>
                      <StarRating
                        rating={synthesisRating}
                        setRating={setSynthesisRating}
                        disabled={synthesisFeedbackSent}
                      />
                      {synthesisRating > 0 &&
                        synthesisRating <= 3 &&
                        !synthesisFeedbackSent && (
                          <div style={{ marginTop: 8 }}>
                            <textarea
                              value={synthesisComment}
                              onChange={(e) =>
                                setSynthesisComment(e.target.value)
                              }
                              placeholder="¿Qué mejorarías en la síntesis generada? ¿Faltó claridad, precisión, profundidad o utilidad? (comentario obligatorio)"
                              rows={2}
                              style={{
                                width: "100%",
                                borderRadius: 6,
                                border: "1px solid #ccc",
                                padding: 8,
                                marginBottom: 8,
                              }}
                            />
                          </div>
                        )}
                      <div style={{ marginTop: 32, textAlign: "right" }}>
                        <button
                          onClick={async () => {
                            // Validación: si alguno de los ratings es <=3, comentario obligatorio
                            if (
                              synthesisRating > 0 &&
                              synthesisRating <= 3 &&
                              (!synthesisComment ||
                                synthesisComment.trim() === "")
                            ) {
                              alert(
                                "Por favor, deja un comentario si tu calificación es de 3 estrellas o menos en alguno de los bloques."
                              );
                              return;
                            }

                            const payload = {
                              feedback_id: idFeedback,
                              // Feedback de syntesis
                              stars_synthe: synthesisRating,
                              feed_synthe:
                                synthesisRating <= 3 ? synthesisComment : "",
                            };

                            fetchData({
                              url: "/feedbacks/stat_synthe",
                              method: "PUT",
                              body: payload,
                            })
                              .catch(() => {
                                alert("Error al enviar feedback");
                              })
                              .then(() => {
                                setSynthesisFeedbackSent(true);
                              });
                          }}
                          disabled={
                            synthesisFeedbackSent || synthesisRating === 0
                          }
                          style={{
                            background: "#009688",
                            color: "white",
                            border: "none",
                            borderRadius: 4,
                            padding: "8px 24px",
                            cursor: synthesisFeedbackSent
                              ? "not-allowed"
                              : "pointer",
                            marginLeft: 12,
                            fontSize: 16,
                          }}
                        >
                          {synthesisFeedbackSent
                            ? "¡Gracias por tu feedback!"
                            : "Enviar feedback"}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </details>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* Agrega en App.css o en un style global: 
@keyframes progressBar {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
.progress-bar-animated {
  animation: progressBar 1.2s linear infinite;
}
*/
