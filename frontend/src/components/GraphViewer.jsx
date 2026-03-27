import React, { useState, useMemo, useRef, useEffect } from "react";
import { InteractiveNvlWrapper } from "@neo4j-nvl/react";
import {
  ClickInteraction,
  DragNodeInteraction,
  HoverInteraction,
  PanInteraction,
  ZoomInteraction
} from '@neo4j-nvl/interaction-handlers';

// Convenciones de colores y formas según tipo y relevancia
function getNodeStyle(node) {
  const type = node.type || "chunk";
  const classification = node.classification || node.relevance || "Relevante";
  let color = "#95E1D3", shape = "dot", size = 15;
  if (type === "root") {
    color = "#FF6B6B"; shape = "star"; size = 35;
  } else if (type === "collection") {
    color = "#4ECDC4"; shape = "square"; size = 25;
  } else if (type === "document") {
    color = "#45B7D1"; shape = "triangle"; size = 20;
  } else {
    // chunk
    if (classification === "Relevante") {
      color = "#95E1D3";
      size = 45; // triple
    } else if (classification === "Relevancia Indeterminada") {
      color = "#FFF9C4";
      size = 30; // doble
    } else {
      color = "#F28C38";
      size = 15; // base
    }
    shape = "dot"; size = 15;
  }
  return { color, shape, size };
}

// Utilidad para convertir el grafo de vis-network a formato NVL
function convertToNVLFormat(graph) {
  const nodeMap = new Map();
  // 1. Agregar todos los nodos primero
  (graph.nodes || []).forEach(n => {
    const id = String(n.id);
    if (id !== undefined && id !== null && id !== "" && id !== "undefined") {
      const style = getNodeStyle(n);
      const tooltip = `<div style='font-family: Arial; padding: 5px;'>`
        + `<strong>${n.label || n.id}</strong><br>`
        + `<strong>Tipo:</strong> ${n.type || 'chunk'}<br>`
        + (n.document_name ? `<strong>Documento:</strong> ${n.document_name}<br>` : '')
        + (n.page ? `<strong>Página:</strong> ${n.page}<br>` : (!n.page && n.type === 'chunk' ? `<span style='color:#3b4a7a;font-size:13px'><b>Resumen de comunidades de chunks realizado por IA</b></span><br>` : ''))
        + (n.score !== undefined ? `<strong>Score:</strong> ${n.score}<br>` : '')
        + (n.classification ? `<strong>Clasificación:</strong> ${n.classification}<br>` : '')
        + (n.llm_summary ? `<strong>Resumen LLM:</strong> ${n.llm_summary}<br>` : '')
        + (n.content ? `<strong>Contenido:</strong> ${n.content.substring(0, 200)}...<br>` : '')
        + `</div>`;
      nodeMap.set(id, {
        id,
        labels: [n.type || "chunk"],
        label: n.label || n.id,
        properties: { ...n, ...style, tooltip }
      });
    }
  });
  let invalidRelCount = 0;
  let rootCandidates = new Set();
  // Detectar posibles nodos centrales (from que no son to)
  const allFrom = new Set((graph.edges || []).map(e => String(e.from ?? e.startNode)).filter(f => f && f !== "undefined"));
  const allTo = new Set((graph.edges || []).map(e => String(e.to ?? e.endNode)).filter(t => t && t !== "undefined"));
  allFrom.forEach(f => { if (!allTo.has(f)) rootCandidates.add(f); });
  // 2. Procesar relaciones y si el nodo referenciado no existe, lo agrego como 'unknown'
  const relationships = (graph.edges || []).reduce((acc, e, idx) => {
    const from = String(e.from ?? e.startNode);
    const to = String(e.to ?? e.endNode);
    let relProps = { ...e };
    if (relProps.properties && typeof relProps.properties === 'object' && !Array.isArray(relProps.properties)) {
      relProps = { ...relProps.properties, ...relProps };
      delete relProps.properties;
    }
    // Si falta el nodo referenciado, lo agrego como 'unknown'
    if (from && !nodeMap.has(from)) {
      nodeMap.set(from, {
        id: from,
        labels: ["unknown"],
        label: from,
        properties: { id: from, label: from, type: "unknown", tooltip: `<div style='font-family: Arial; padding: 5px;'><strong>${from}</strong><br><strong>Tipo:</strong> unknown</div>` }
      });
    }
    if (to && !nodeMap.has(to)) {
      nodeMap.set(to, {
        id: to,
        labels: ["unknown"],
        label: to,
        properties: { id: to, label: to, type: "unknown", tooltip: `<div style='font-family: Arial; padding: 5px;'><strong>${to}</strong><br><strong>Tipo:</strong> unknown</div>` }
      });
    }
    if (
      from !== undefined && from !== null && from !== "" && from !== "undefined" &&
      to !== undefined && to !== null && to !== "" && to !== "undefined" &&
      nodeMap.has(from) && nodeMap.has(to)
    ) {
      acc.push({
        id: relProps.id ? String(relProps.id) : `rel_${idx}`,
        type: relProps.label || relProps.type || "RELATES_TO",
        from,
        to,
        properties: relProps
      });
    } else {
      invalidRelCount++;
      console.warn("Relación inválida ignorada:", e);
    }
    return acc;
  }, []);
  // Si hay rootCandidates que no están en nodeMap, agrégalos explícitamente
  rootCandidates.forEach(rootId => {
    if (rootId !== undefined && rootId !== null && rootId !== "" && rootId !== "undefined" && !nodeMap.has(rootId)) {
      const style = getNodeStyle({ id: rootId, type: "root" });
      nodeMap.set(rootId, {
        id: rootId,
        labels: ["root"],
        label: rootId,
        properties: { id: rootId, label: rootId, type: "root", ...style, tooltip: `<div style='font-family: Arial; padding: 5px;'><strong>${rootId}</strong><br><strong>Tipo:</strong> root</div>` }
      });
    }
  });
  // Filtrar nodos con id inválido
  const nodes = Array.from(nodeMap.values()).filter(n => n.id !== undefined && n.id !== null && n.id !== "" && n.id !== "undefined");
  // Log de depuración
  console.log("[NVL-convert] Nodos convertidos:", nodes);
  console.log("[NVL-convert] Relaciones convertidas:", relationships);
  return { nodes, relationships, invalidRelCount };
}

// Leyenda visual para los tipos de nodo
function GraphLegend() {
  const legend = [
    { color: "#FF6B6B", shape: "★", label: "Root (Ley)" },
    { color: "#4ECDC4", shape: "■", label: "Colección" },
    { color: "#45B7D1", shape: "▲", label: "Documento" },
    { color: "#95E1D3", shape: "●", label: "Chunk relevante" },
    { color: "#FFF9C4", shape: "●", label: "Chunk indeterminado" },
    { color: "#F28C38", shape: "●", label: "Chunk no relevante" }
  ];
  return (
    <div style={{ display: 'flex', gap: 18, alignItems: 'center', margin: '12px 0 8px 0', fontSize: 15 }}>
      <span style={{ fontWeight: 600, marginRight: 8 }}>Leyenda:</span>
      {legend.map((item, i) => (
        <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ color: item.color, fontSize: 22, fontWeight: 700 }}>{item.shape}</span>
          <span style={{ color: '#333' }}>{item.label}</span>
        </span>
      ))}
    </div>
  );
}

export default function GraphViewer({ graph }) {
  // Log raw graph received from backend
  console.log("[NVL] Raw graph received from backend:", graph);
  const [nodeDetails, setNodeDetails] = useState(null);
  const [layoutKey, setLayoutKey] = useState(0);
  const nvlRef = useRef();

  const handleZoomIn = () => {
    if (nvlRef.current && nvlRef.current.api) {
      nvlRef.current.api.zoomIn();
    }
  };

  const handleZoomOut = () => {
    if (nvlRef.current && nvlRef.current.api) {
      nvlRef.current.api.zoomOut();
    }
  };

  // Re-trigger layout when graph changes
  useEffect(() => {
    setLayoutKey(x => x + 1);
    setNodeDetails(null);
  }, [graph]);

  // Sustituir el grafo real por el de prueba temporalmente
  const { nodes: nvlNodes, relationships: nvlRels, invalidRelCount } = useMemo(() => {
    return convertToNVLFormat(graph); // USAR EL GRAFO REAL
  }, [graph]);

  // Debug: print nodes and relationships to console
  useEffect(() => {
    if (nvlNodes && nvlRels) {
      console.log("[NVL] Nodes:", nvlNodes);
      console.log("[NVL] Relationships:", nvlRels);
    }
  }, [nvlNodes, nvlRels]);

  // Forzar el recalculo del layout de NVL cuando cambian los nodos/relaciones
  useEffect(() => {
    if (nvlRef.current && typeof nvlRef.current.fit === 'function') {
      setTimeout(() => nvlRef.current.fit(), 300);
    }
  }, [nvlNodes, nvlRels]);

  if (!graph) return <div style={{color:'red',margin:'32px 0'}}>No se recibió grafo para visualizar.</div>;
  if (!nvlNodes.length || !nvlRels.length) {
    return <div style={{color:'red',margin:'32px 0'}}>El grafo recibido no contiene nodos o relaciones válidas para mostrar.</div>;
  }
  return (
    <div style={{ margin: "32px 0" }}>
      <h3>Grafo Interactivo de Resultados</h3>
      <GraphLegend />
      <div style={{ margin: '8px 0' }}>
        <button onClick={handleZoomIn} style={{ marginRight: 8 }}>Acercar</button>
        <button onClick={handleZoomOut}>Alejar</button>
      </div>
      {invalidRelCount > 0 && (
        <div style={{ color: 'red', fontWeight: 600, marginBottom: 8 }}>
          Advertencia: {invalidRelCount} relación(es) inválida(s) fueron ignoradas por contener nodos no definidos.
        </div>
      )}
      <div style={{ width: "100%", height: 600, border: "1px solid #ccc", borderRadius: 8, background: "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)" }}>
        <InteractiveNvlWrapper
          key={layoutKey}
          ref={nvlRef}
          nodes={nvlNodes}
          rels={nvlRels}
          nvlOptions={{
            layout: "forceDirected",
            disableTelemetry: true,
            initialZoom: 0.9,
            renderer: "canvas", // Fuerza renderizado 2D para evitar problemas de WebGL
            interaction: {
              dragNodes: true,
              dragView: true,
              zoomView: true,
              tooltipDelay: 200,
              selectOnClick: true,
              drawShadowOnHover: true
            },
            physics: {
              enabled: true,
              solver: "forceAtlas2Based"
            }
          }}
          mouseEventCallbacks={{
            onNodeClick: node => setNodeDetails(node.properties || node),
            onBackgroundClick: () => setNodeDetails(null)
          }}
        />
      </div>
      <div style={{ fontSize: 14, color: "#555", marginTop: 8 }}>
        Haz clic en los nodos para ver detalles.
      </div>
      {nodeDetails && (
        <div style={{ marginTop: 20, background: "#f8f8f8", padding: 16, borderRadius: 8, maxHeight: 350, overflowY: 'auto', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
          <h4>Detalles del Nodo Seleccionado</h4>
          {nodeDetails.tooltip ? (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 15, border: '1px solid #ddd', borderRadius: 6, background: '#fff', padding: 10 }}
                   dangerouslySetInnerHTML={{ __html: nodeDetails.tooltip }} />
            </div>
          ) : null}
          <table style={{ width: '100%', fontSize: 15, borderCollapse: 'collapse' }}>
            <tbody>
              {Object.entries(nodeDetails).filter(([key]) => key !== 'tooltip').map(([key, value]) => (
                <tr key={key}>
                  <td style={{ fontWeight: 600, padding: '4px 8px', verticalAlign: 'top', color: '#333' }}>{key}</td>
                  <td style={{ padding: '4px 8px', color: '#444' }}>{typeof value === 'object' && value !== null ? JSON.stringify(value, null, 2) : String(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
