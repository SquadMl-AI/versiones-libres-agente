import React, { useState } from 'react';
import { chatWithBackend } from '../api';

export default function SherlockTab() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      const userEmail = sessionStorage.getItem("userEmail");
      const response = await chatWithBackend(newMessages, userEmail);
      const assistantMessage = response; 
      setMessages(prevMessages => [...prevMessages, assistantMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage = { role: 'assistant', content: 'Error: No se pudo obtener una respuesta.' };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", display: 'flex', flexDirection: 'column', height: 'calc(100vh - 200px)' }}>
      <h2>Pregúntale a Sherlock</h2>
      <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #ccc', borderRadius: 8, padding: 16, marginBottom: 16 }}>
        {messages.map((msg, index) => (
          <div key={index} style={{ marginBottom: 12, textAlign: msg.role === 'user' ? 'right' : 'left' }}>
            <div style={{
              display: 'inline-block',
              padding: '8px 12px',
              borderRadius: 12,
              backgroundColor: msg.role === 'user' ? '#dcf8c6' : '#f1f0f0',
              maxWidth: '70%',
            }}>
              {msg.content}
            </div>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex' }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && !loading && handleSend()}
          placeholder="Escribe tu mensaje..."
          style={{ flex: 1, padding: '10px', borderRadius: 8, border: '1px solid #ccc' }}
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading} style={{ marginLeft: 8, padding: '10px 20px', borderRadius: 8, border: 'none', backgroundColor: '#4ECDC4', color: 'white', cursor: 'pointer' }}>
          {loading ? 'Enviando...' : 'Enviar'}
        </button>
      </div>
    </div>
  );
}
