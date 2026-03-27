import React, { useEffect, useRef, useState, useCallback } from "react";

// Forzar el uso de la CDN de vis-network
const visNetworkUrl =
  "https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js";
const visCssUrl = "/vis-network.css"; // Usar el CSS local

export default function VisNetworkGraph({ threeData }) {
  const containerRef = useRef(null);
  const [graph, setGraph] = useState(null);
  const [visLoaded, setVisLoaded] = useState(!!window.vis);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState("");
  const [legendVisible, setLegendVisible] = useState(true);
  const [relevanceFilters, setRelevanceFilters] = useState({
    Relevante: true,
    "Relevancia Indeterminada": true,
    "No Relevante": false,
    "No Analizado": false,
  });
  const [fullscreen, setFullscreen] = useState(false);

  useEffect(() => {
    // Carga dinámica de vis-network si no está en window
    if (!window.vis) {
      // Evita cargar múltiples veces
      if (!document.getElementById("vis-network-script")) {
        const script = document.createElement("script");
        script.src = visNetworkUrl;
        script.async = false;
        script.id = "vis-network-script";
        script.onload = () => setVisLoaded(true);
        document.body.appendChild(script);
      } else {
        // Si el script ya está pero aún no está window.vis, espera a que cargue
        const checkVis = setInterval(() => {
          if (window.vis) {
            setVisLoaded(true);
            clearInterval(checkVis);
          }
        }, 50);
        return () => clearInterval(checkVis);
      }
      // Carga la hoja de estilos si no está
      if (!document.getElementById("vis-network-css")) {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = visCssUrl;
        link.id = "vis-network-css";
        document.head.appendChild(link);
      }
    } else {
      setVisLoaded(true);
    }
  }, []);

  useEffect(() => {
    if (visLoaded && graph) {
      renderNetwork(graph);
    }
    // eslint-disable-next-line
  }, [visLoaded, graph, relevanceFilters]);

  const label = useCallback((type, node, id) => {
    switch (type) {
      case "root":
        return "Sentencias Ley 975";
      case "chunk":
        return node?.page_numbers ? "Pág." + node.page_numbers[0] : id;
      default:
        return id;
    }
  }, []);

  const formatGraphForVis = useCallback(
    (root) => {
      const nodes = [];
      const edges = [];

      function traverse(node, parentId = null, level = 0) {
        const nodeId =
          node["chunk id"] || node.id || Math.random().toString(36).substr(2, 9);

        // Tipo según nivel
        const levelTypeMap = {
          0: "root",
          1: "collection",
          2: "document",
        };
        const type =
          levelTypeMap[level] || (node.page_numbers ? "chunk" : "unknown");

        // Crear nodo
        nodes.push({
          id: nodeId,
          label: label(type, node, nodeId),
          type: type,
          ...node,
        });

        // Crear arista si tiene padre
        if (parentId) {
          edges.push({ from: parentId, to: nodeId });
        }

        // CASO DOCUMENTO (nivel 2)
        if (type === "document" && Array.isArray(node.children)) {
          const chunks = node.children;

          // Agrupar por categoria
          const byCategoria = {};
          for (const chunk of chunks) {
            const cat = chunk.categoria || "sin_categoria";
            if (!byCategoria[cat]) byCategoria[cat] = [];
            byCategoria[cat].push(chunk);
          }

          // Procesar cada categoria
          for (const [, catChunks] of Object.entries(byCategoria)) {
            // Agrupar por primera página
            const byPage = {};
            for (const chunk of catChunks) {
              const page = Array.isArray(chunk.page_numbers)
                ? chunk.page_numbers[0]
                : 0;
              if (!byPage[page]) byPage[page] = [];
              byPage[page].push(chunk);
            }
            // Si las páginas son diferentes → ordenadas y en cadena
            if (Object.keys(byPage).length > 1) {
              const pagesOrdenadas = Object.keys(byPage).sort((a, b) => a - b);

              let anteriorId = null;
              for (const page of pagesOrdenadas) {
                const grupo = byPage[page];

                for (const chunk of grupo) {
                  const chunkId = chunk["chunk id"];
                  nodes.push({
                    id: chunkId,
                    label: label("chunk", chunk, chunkId),
                    type: "chunk",
                    ...chunk,
                  });

                  if (anteriorId) {
                    edges.push({ from: anteriorId, to: chunkId });
                  } else {
                    edges.push({ from: nodeId, to: chunkId });
                  }

                  anteriorId = chunkId;
                }
              }
            } else {
              // Si todas están en la misma página → conectar directo al documento
              for (const chunk of catChunks) {
                const chunkId = chunk["chunk id"];
                nodes.push({
                  id: chunkId,
                  label: label("chunk", chunk, chunkId),
                  type: "chunk",
                  ...chunk,
                });

                edges.push({ from: nodeId, to: chunkId });
              }
            }
          }
        }

        // CASO NORMAL: seguir bajando si hay hijos
        if (type !== "document" && Array.isArray(node.children)) {
          for (const child of node.children) {
            traverse(child, nodeId, level + 1);
          }
        }
      }

      traverse(root);
      return { nodes, edges };
    },
    [label]
  );

  useEffect(() => {
    if (threeData) {
      const graph = formatGraphForVis(threeData);
      setGraph(graph);
    }
  }, [threeData, formatGraphForVis]);

  function renderNetwork(graph) {
    if (!window.vis || !containerRef.current || !graph) return;
    containerRef.current.innerHTML = "";
    // 1. Filtrar nodos chunk según los filtros de relevancia
    const visibleChunks = (graph.nodes || []).filter(
      (n) =>
        n.type == "chunk" &&
        Object.keys(relevanceFilters)
          .filter((key) => relevanceFilters[key])
          .map((key) => key.toLowerCase()) // convertir todas las claves a minúsculas
          .includes(n.categoria.toLowerCase()) // comparar con n.categoria en minúsculas
    );
    const visibleChunkIds = new Set(visibleChunks.map((n) => n.id));
    // 2. Encontrar documentos padres de los chunks visibles
    const docIdsFromEdges = new Set();
    (graph.edges || []).forEach((e) => {
      if (visibleChunkIds.has(e.to)) docIdsFromEdges.add(e.from);
    });
    const visibleDocs = (graph.nodes || []).filter(
      (n) => n.type === "document" && docIdsFromEdges.has(n.id)
    );
    const visibleDocIds = new Set(visibleDocs.map((n) => n.id));
    // 3. Encontrar colecciones padres de los documentos visibles
    const collIdsFromEdges = new Set();
    (graph.edges || []).forEach((e) => {
      if (visibleDocIds.has(e.to)) collIdsFromEdges.add(e.from);
    });
    const visibleColls = (graph.nodes || []).filter(
      (n) => n.type === "collection" && collIdsFromEdges.has(n.id)
    );
    // 4. Siempre mostrar raíz y consulta
    const visibleSpecials = (graph.nodes || []).filter(
      (n) => n.type === "root" || n.type === "query"
    );
    // 5. Unir todos los nodos visibles
    const filteredNodes = [
      ...visibleChunks,
      ...visibleDocs,
      ...visibleColls,
      ...visibleSpecials,
    ];
    const visibleNodeIds = new Set(filteredNodes.map((n) => n.id));
    // 6. Filtrar aristas: solo si ambos nodos están visibles
    const filteredEdges = (graph.edges || []).filter(
      (e) => visibleNodeIds.has(e.from) && visibleNodeIds.has(e.to)
    );
    const nodes = new window.vis.DataSet(
      filteredNodes.map((n) => {
        let label;
        if (n.type === "chunk") {
          // Usar siempre la propiedad page si existe y no es "N/A"
          let pageValue = n.page_numbers;
          if (Array.isArray(pageValue) && pageValue.length > 0) {
            label = String(pageValue[0]);
          } else if (pageValue && pageValue !== "N/A") {
            if (typeof pageValue === "string" && pageValue.includes(",")) {
              // Si es string tipo "1,2,3", tomar el primer valor
              label = pageValue.split(",")[0].trim();
            } else {
              label = String(pageValue);
            }
          } else if (typeof n.id === "string") {
            // Fallback: extraer el último número del id
            const match = n.id.match(/(\d+)(?!.*\d)/);
            label = match ? match[1] : "Chunk";
          } else {
            label = "Chunk";
          }
        } else {
          label = n.label || n.id;
        }
        return {
          id: n.id,
          label,
          // Nueva simbología moderna y diferenciada
          color:
            n.type === "root"
              ? "#4A90E2" // Azul corporativo
              : n.type === "collection"
              ? "#50E3C2" // Verde azulado (Teal)
              : n.type === "document"
              ? "#F5A623" // Naranja
              : n.categoria === "Relevante"
              ? "#2ECC71" // Verde esmeralda
              : n.categoria === "Relevancia Indeterminada"
              ? "#F1C40F" // Amarillo girasol
              : typeof n.categoria === "string" &&
                n.categoria.trim() === "No Relevante"
              ? { background: "#ECF0F1", border: "#95A5A6" } // Gris claro con borde plateado
              : typeof n.categoria === "string" &&
                n.categoria.trim() === "No Analizado"
              ? { background: "#9e9e9e", border: "#313030" } // Gris claro con borde plateado
              : n.type === "chunk" &&
                (!n.categoria || n.categoria === null || n.categoria === "")
              ? { background: "#3498DB", border: "#2980B9" } // Azul neutro
              : { background: "#9e9e9e", border: "#313030" }, // Fallback
          borderWidth:
            typeof n.categoria === "string" &&
            n.categoria.trim() === "No Relevante"
              ? 2
              : 1,
          shape:
            n.type === "root"
              ? "star"
              : n.type === "collection"
              ? "square"
              : n.type === "document"
              ? "triangle"
              : "dot",
          size:
            n.type === "root"
              ? 35
              : n.type === "collection"
              ? 25
              : n.type === "document"
              ? 20
              : n.categoria === "Relevante"
              ? 28 // Tamaño grande para destacar
              : n.categoria === "Relevancia Indeterminada"
              ? 15
              : typeof n.categoria === "string" &&
                n.categoria.trim() === "No Relevante"
              ? 12 // Ligeramente más pequeño
              : n.type === "chunk" &&
                (!n.categoria || n.categoria === null || n.categoria === "")
              ? (() => {
                  // Escalar el tamaño de acuerdo al reranker_score (mínimo 8, máximo 22)
                  const minSize = 8;
                  const maxSize = 22;
                  let score =
                    typeof n.reranker_score === "number"
                      ? n.reranker_score
                      : parseFloat(n.reranker_score);
                  if (isNaN(score)) score = 0;
                  // Normalizar el score entre 0 y 1 usando el score máximo de los chunks visibles
                  let maxScore = 1;
                  if (Array.isArray(graph.nodes)) {
                    const scores = graph.nodes
                      .filter(
                        (x) =>
                          x.type === "chunk" &&
                          (!x.categoria ||
                            x.categoria === null ||
                            x.categoria === "")
                      )
                      .map((x) =>
                        typeof x.reranker_score === "number"
                          ? x.reranker_score
                          : parseFloat(x.reranker_score)
                      )
                      .filter((x) => !isNaN(x));
                    if (scores.length > 0) maxScore = Math.max(...scores);
                  }
                  const norm = maxScore > 0 ? score / maxScore : 0;
                  return minSize + (maxSize - minSize) * norm;
                })()
              : 15, // Default para chunks
          title: n.resumen_llm || label || n.id,
          ...n,
        };
      })
    );
    const edges = new window.vis.DataSet(
      filteredEdges.map((e) => ({
        from: e.from,
        to: e.to,
        arrows: "to",
        color: { color: "#888" },
        label: "", // No mostrar texto en las relaciones
      }))
    );
    const data = { nodes, edges };
    const options = {
      physics: { enabled: true, solver: "forceAtlas2Based" },
      interaction: { dragNodes: true, dragView: true, zoomView: true },
      layout: { improvedLayout: true },
    };
    const network = new window.vis.Network(containerRef.current, data, options);
    network.on("click", function (params) {
      if (params.nodes.length) {
        const nodeId = params.nodes[0];
        const node = nodes.get(nodeId);
        let html = `<div style='font-family: Arial; font-size: 16px;'><b>${
          node.label || node.id
        }</b><br/>`;
        if (node.type === "chunk") {
          // Página (solo la primera si es lista o string con comas)
          let pageValue = node.page_numbers || node["Pág."] || node["Página"];
          let page = "";
          if (Array.isArray(pageValue) && pageValue.length > 0) {
            page = String(pageValue[0]);
          } else if (typeof pageValue === "string" && pageValue.includes(",")) {
            page = pageValue.split(",")[0].trim();
          } else if (pageValue && pageValue !== "N/A") {
            page = String(pageValue);
          }
          // Mostrar metadatos principales en orden: Colección, Documento, Página
          if (node.folder) {
            html += `<div style='margin:8px 0;'><b>Colección:</b> <span style='color:#3b4a7a;'>${node.folder}</span></div>`;
          }
          if (node.document_name) {
            html += `<div style='margin:8px 0;'><b>Documento:</b> <span style='color:#3b4a7a;'>${node.document_name}</span></div>`;
          }
          if (page) {
            html += `<div style='margin:8px 0;'><b>Página:</b> <span style='color:#3b4a7a;'>${page}</span></div>`;
          }
          // Resumen de relevancia
          if (node.resumen_llm || node.content) {
            html += `<div style='margin:8px 0;'><b>Resumen del análisis de relevancia:</b><br/><span style='color:#333;'>${
              node.resumen_llm || node.content
            }</span></div>`;
          }
          if (node.categoria) {
            html += `<div style='margin:8px 0;'><b>Categoria:</b><br/><span style='color:#333;'>${node.categoria}</span></div>`;
          }
          // Texto original del chunk
          if (node.content) {
            html += `<div style='margin:8px 0;'><b>Texto original del chunk:</b><br/><span style='color:#333; white-space:pre-wrap;'>${node.content}</span></div>`;
          }
        } else {
          // Para otros tipos de nodo, mostrar solo el label y tipo
          html += `<div style='margin:8px 0; color:#555;'><b>Tipo:</b> ${
            node.type || "N/A"
          }</div>`;
        }
        html += `</div>`;
        setModalContent(removeThinkBlocks(html));
        setModalOpen(true);
      }
    });
  }

  // Utilidad para filtrar bloques <think>...</think> de cualquier string
  function removeThinkBlocks(text) {
    if (typeof text !== "string") return text;
    return text.replace(/<think>[\s\S]*?<\/think>/gi, "").trim();
  }

  // Manejar pantalla completa
  function handleFullscreen() {
    setFullscreen((f) => !f);
    setTimeout(() => {
      if (!fullscreen && containerRef.current) {
        containerRef.current.scrollIntoView({ behavior: "smooth" });
      }
    }, 200);
  }

  return (
    <div
      style={{
        width: "100%",
        height: fullscreen ? "100vh" : 700,
        maxHeight: fullscreen ? "100vh" : 700,
        position: fullscreen ? "fixed" : "relative",
        top: fullscreen ? 0 : undefined,
        left: fullscreen ? 0 : undefined,
        zIndex: fullscreen ? 2000 : undefined,
        background: fullscreen
          ? "#f5f7fa"
          : "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
        border: fullscreen ? "none" : "1px solid #ccc",
        borderRadius: fullscreen ? 0 : 8,
        margin: fullscreen ? 0 : "32px 0",
      }}
    >
      <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
      {!visLoaded && (
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: 0,
            bottom: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#888",
          }}
        >
          Cargando grafo...
        </div>
      )}
      {modalOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            background: "rgba(0,0,0,0.4)",
            zIndex: 1000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
          onClick={() => setModalOpen(false)}
        >
          <div
            style={{
              background: "#fff",
              borderRadius: 10,
              padding: 32,
              minWidth: 320,
              maxWidth: 600,
              maxHeight: 500,
              overflowY: "auto",
              boxShadow: "0 4px 24px rgba(0,0,0,0.2)",
              position: "relative",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              style={{
                position: "absolute",
                top: 10,
                right: 10,
                background: "#4ECDC4",
                color: "#fff",
                border: "none",
                borderRadius: 5,
                padding: "4px 12px",
                cursor: "pointer",
                fontWeight: 600,
                fontSize: 18,
              }}
              onClick={() => setModalOpen(false)}
            >
              ×
            </button>
            <div dangerouslySetInnerHTML={{ __html: modalContent }} />
          </div>
        </div>
      )}
      {/* Leyenda barra inferior con filtros */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 0,
          width: "100%",
          background: "rgba(255,255,255,0.97)",
          borderTop: "1px solid #ddd",
          boxShadow: "0 -2px 12px rgba(0,0,0,0.06)",
          padding: legendVisible ? "10px 0 10px 0" : "6px 0 6px 0",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          minHeight: legendVisible ? 48 : 24,
          transition: "min-height 0.2s, padding 0.2s",
          zIndex: 10,
        }}
      >
        {legendVisible && (
          <>
            <div
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 32,
                marginBottom: 8,
              }}
            >
              <LegendItem
                color="#4A90E2"
                shape="star"
                label="Raíz (Sentencias Ley 975)"
              />
              <LegendItem color="#000" shape="diamond" label="Consulta" />
              <LegendItem color="#50E3C2" shape="square" label="Colección" />
              <LegendItem color="#F5A623" shape="triangle" label="Documento" />
              <LegendItem color="#2ECC71" shape="dot" label="Chunk Relevante" />
              <LegendItem
                color="#F1C40F"
                shape="dot"
                label="Chunk Relevancia Indeterminada"
              />
              <LegendItem
                color="#ECF0F1"
                border="#95A5A6"
                shape="dot"
                label="Chunk No Relevante"
              />
              <LegendItem
                color="#9E9E9E"
                shape="dot"
                label="Chunk No Analizado"
              />
            </div>
            {/* Filtros de relevancia debajo de la leyenda */}
            <div
              style={{
                display: "flex",
                flexDirection: "row",
                alignItems: "center",
                gap: 12,
                background: "rgba(255,255,255,0.0)",
                borderRadius: 6,
                padding: "0 8px",
                marginBottom: 8,
              }}
            >
              <span style={{ fontWeight: 600, fontSize: 14, marginRight: 4 }}>
                Filtrar relevancia:
              </span>
              {Object.entries(relevanceFilters).map(([key, val]) => (
                <label
                  key={key}
                  style={{
                    fontSize: 13,
                    display: "flex",
                    alignItems: "center",
                    gap: 4,
                  }}
                >
                  <input
                    type="checkbox"
                    checked={val}
                    onChange={(e) =>
                      setRelevanceFilters((f) => ({
                        ...f,
                        [key]: e.target.checked,
                      }))
                    }
                    style={{
                      accentColor:
                        key === "Relevante"
                          ? "#2ECC71"
                          : key === "Relevancia Indeterminada"
                          ? "#F1C40F"
                          : key === "No Relevante"
                          ? "#95a5a6"
                          : "#313030",
                    }}
                  />
                  {key}
                </label>
              ))}
            </div>
          </>
        )}
        <div
          style={{
            width: "100%",
            display: "flex",
            justifyContent: "center",
            marginTop: legendVisible ? 0 : 0,
            gap: 12,
          }}
        >
          <button
            onClick={() => setLegendVisible((v) => !v)}
            style={{
              background: "#fff",
              color: "#222",
              border: "1.5px solid #888",
              borderRadius: 6,
              padding: "4px 18px",
              fontSize: 16,
              cursor: "pointer",
              fontWeight: 600,
              boxShadow: "0 2px 6px rgba(0,0,0,0.08)",
              zIndex: 11,
              marginBottom: legendVisible ? 2 : 0,
              marginTop: legendVisible ? 0 : 2,
              transition: "background 0.2s, color 0.2s, border 0.2s",
            }}
            title={legendVisible ? "Ocultar leyenda" : "Mostrar leyenda"}
          >
            {legendVisible ? "Ocultar leyenda" : "Mostrar leyenda"}
          </button>
          <button
            onClick={handleFullscreen}
            style={{
              background: fullscreen ? "#4A90E2" : "#fff",
              color: fullscreen ? "#fff" : "#222",
              border: "1.5px solid #888",
              borderRadius: 6,
              padding: "4px 18px",
              fontSize: 16,
              cursor: "pointer",
              fontWeight: 600,
              boxShadow: "0 2px 6px rgba(0,0,0,0.08)",
              zIndex: 11,
              marginBottom: legendVisible ? 2 : 0,
              marginTop: legendVisible ? 0 : 2,
              transition: "background 0.2s, color 0.2s, border 0.2s",
            }}
            title={
              fullscreen ? "Salir de pantalla completa" : "Pantalla completa"
            }
          >
            {fullscreen ? "Salir de pantalla completa" : "Pantalla completa"}
          </button>
        </div>
      </div>
    </div>
  );
}

// Componente auxiliar para cada ítem de la leyenda
function LegendItem({ color, border, shape, label }) {
  let shapeStyle = {};
  if (shape === "star") {
    shapeStyle = {
      width: 22,
      height: 22,
      background: "none",
      display: "inline-block",
    };
    return (
      <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
        <svg width="22" height="22" viewBox="0 0 22 22">
          <polygon
            points="11,2 13,8 19,8 14,12 16,18 11,14 6,18 8,12 3,8 9,8"
            fill={color}
            stroke="#313030"
            strokeWidth="1.2"
          />
        </svg>
        <span style={{ fontSize: 14 }}>{label}</span>
      </span>
    );
  }
  if (shape === "diamond") {
    shapeStyle = {
      width: 18,
      height: 18,
      background: "none",
      display: "inline-block",
    };
    return (
      <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
        <svg width="18" height="18" viewBox="0 0 18 18">
          <polygon
            points="9,2 16,9 9,16 2,9"
            fill={color}
            stroke="#333"
            strokeWidth="1.2"
          />
        </svg>
        <span style={{ fontSize: 14 }}>{label}</span>
      </span>
    );
  }
  if (shape === "square") {
    shapeStyle = {
      width: 16,
      height: 16,
      background: color,
      border: "1.5px solid #333",
      display: "inline-block",
      borderRadius: 3,
    };
    return (
      <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
        <span style={shapeStyle}></span>
        <span style={{ fontSize: 14 }}>{label}</span>
      </span>
    );
  }
  if (shape === "triangle") {
    return (
      <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
        <svg width="18" height="18" viewBox="0 0 18 18">
          <polygon
            points="9,3 16,15 2,15"
            fill={color}
            stroke="#333"
            strokeWidth="1.2"
          />
        </svg>
        <span style={{ fontSize: 14 }}>{label}</span>
      </span>
    );
  }
  // dot
  shapeStyle = {
    width: 16,
    height: 16,
    background: color,
    border: border ? `2px solid ${border}` : "1.5px solid #333",
    borderRadius: "50%",
    display: "inline-block",
  };
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
      <span style={shapeStyle}></span>
      <span style={{ fontSize: 14 }}>{label}</span>
    </span>
  );
}
