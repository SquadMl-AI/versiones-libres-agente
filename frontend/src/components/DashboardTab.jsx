
import React, { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend
} from "recharts";

import { BACKEND_URL } from "../api";

function DashboardTab() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/v1/dashboard/metrics`)
      .then((res) => res.json())
      .then((data) => {
        setMetrics(data);
        setLoading(false);
      })
      .catch((err) => {
        setError("Error al cargar métricas: " + err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div style={{textAlign:'center', marginTop:40}}>Cargando métricas...</div>;
  if (error) return <div style={{color: 'red', textAlign:'center', marginTop:40}}>{error}</div>;
  if (!metrics) return <div style={{textAlign:'center', marginTop:40}}>No hay datos de métricas.</div>;

  const feedbackSplit = metrics.feedback_split || {};
  const totalConFeedback = feedbackSplit.true || 0;
  const totalSinFeedback = feedbackSplit.false || 0;

  // Colores para tarjetas
  const cardStyle = {
    display: 'flex', gap: 18, flexWrap: 'wrap', margin: '24px 0 32px 0', justifyContent: 'center'
  };
  const kpiBox = {
    background: '#f5f7fa', border: '1px solid #e0e0e0', borderRadius: 10, minWidth: 180, minHeight: 90,
    boxShadow: '0 2px 8px #e3e3e3', padding: '1.1em 1.2em', textAlign: 'center', flex: '1 1 180px',
    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
  };
  const kpiValue = { fontSize: 28, fontWeight: 700, color: '#1a237e', marginBottom: 2 };
  const kpiLabel = { fontSize: 15, color: '#444', marginBottom: 0 };

  return (
    <div style={{maxWidth: 900, margin: '0 auto', padding: '2em 1em'}}>
      <h2 style={{ color: '#1a237e', marginBottom: 8 }}>Indicadores de Uso y Feedback</h2>
      <div style={cardStyle}>
        <div style={kpiBox}>
          <span style={kpiValue}>{metrics.total_interactions}</span>
          <span style={kpiLabel}>Total de interacciones</span>
        </div>
        <div style={kpiBox}>
          <span style={kpiValue}>{metrics.avg_synthesis_feedback?.toFixed(2) ?? 'N/A'}</span>
          <span style={kpiLabel}>Promedio síntesis</span>
        </div>
        <div style={kpiBox}>
          <span style={kpiValue}>{metrics.avg_graph_feedback?.toFixed(2) ?? 'N/A'}</span>
          <span style={kpiLabel}>Promedio grafo</span>
        </div>
        <div style={{...kpiBox, background:'#e8f5e9', border:'1px solid #b2dfdb'}}>
          <span style={{...kpiValue, color:'#388e3c'}}>
            <span role="img" aria-label="feedback">👍</span> {totalConFeedback}
          </span>
          <span style={kpiLabel}>Con feedback explícito</span>
        </div>
        <div style={{...kpiBox, background:'#fff3e0', border:'1px solid #ffe0b2'}}>
          <span style={{...kpiValue, color:'#f57c00'}}>
            <span role="img" aria-label="no-feedback">🕵️‍♂️</span> {totalSinFeedback}
          </span>
          <span style={kpiLabel}>Sin feedback explícito</span>
        </div>
      </div>

      <div style={{display:'flex', flexWrap:'wrap', gap:32, marginBottom:32}}>
        <div style={{flex:'1 1 320px', minWidth:260}}>
          <h4 style={{color:'#1565c0', marginBottom:8}}>Distribución por tipo de feedback</h4>
          <ul style={{paddingLeft:22, marginTop:0}}>
            {Object.entries(metrics.feedback_type_distribution || {}).map(([type, count]) => (
              <li key={type}><b>{type || '(vacío)'}:</b> {count}</li>
            ))}
          </ul>
        </div>
        <div style={{flex:'1 1 320px', minWidth:260}}>
          <h4 style={{color:'#1565c0', marginBottom:8}}>Distribución por versión de cliente</h4>
          <ul style={{paddingLeft:22, marginTop:0}}>
            {Object.entries(metrics.client_version_distribution || {}).map(([ver, count]) => (
              <li key={ver}><b>{ver || '(vacío)'}:</b> {count}</li>
            ))}
          </ul>
        </div>
      </div>

      <div style={{marginBottom:32}}>
        <h4 style={{color:'#1565c0', marginBottom:8}}>Evolución de interacciones (últimos 30 días)</h4>
        <div style={{width:'100%', height:320, maxWidth:700, margin:'0 auto 18px auto', background:'#fafbfc', borderRadius:8, boxShadow:'0 1px 6px #e3e3e3', padding:'1em 1.5em'}}>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart
              data={(metrics.evolution_last_30_days || metrics.interactions_last_30_days || []).map(row => ({
                date: row.date || row[0],
                count: row.count ?? row[1]
              }))}
              margin={{ top: 20, right: 30, left: 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="date" tick={{fontSize:12}} angle={-30} textAnchor="end" height={50} />
              <YAxis allowDecimals={false} tick={{fontSize:13}} />
              <Tooltip formatter={(value) => [value, 'Interacciones']} labelFormatter={label => `Fecha: ${label}`} />
              <Line type="monotone" dataKey="count" stroke="#1976d2" strokeWidth={3} dot={{r:2}} activeDot={{r:5}} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div style={{overflowX:'auto'}}>
          <table style={{borderCollapse:'collapse', minWidth:340, width:'100%', background:'#fafbfc', fontSize:'1em'}}>
            <thead>
              <tr style={{background:'#e3eafc'}}>
                <th style={{padding:'6px 12px', border:'1px solid #d1d5db'}}>Fecha</th>
                <th style={{padding:'6px 12px', border:'1px solid #d1d5db'}}>Interacciones</th>
              </tr>
            </thead>
            <tbody>
              {(metrics.evolution_last_30_days || metrics.interactions_last_30_days || []).map((row, i) => (
                <tr key={i} style={{background: i%2===0 ? '#f5f7fa' : '#fff'}}>
                  <td style={{padding:'6px 12px', border:'1px solid #e0e0e0'}}>{row.date || row[0]}</td>
                  <td style={{padding:'6px 12px', border:'1px solid #e0e0e0'}}>{row.count ?? row[1]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div style={{marginTop:24, color:'#616161', fontSize:'0.98em', textAlign:'right'}}>
        Última actualización: {new Date().toLocaleDateString('es-CO', {year:'numeric', month:'long', day:'numeric'})}
      </div>
    </div>
  );
}

export default DashboardTab;
