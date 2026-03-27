import React, { useState, useEffect, useRef } from 'react';

const MultiSelect = ({ options, selected, onChange, placeholder }) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);

  const handleSelect = (option) => {
    if (selected.find(s => s.id === option.id)) {
      onChange(selected.filter(s => s.id !== option.id));
    } else {
      onChange([...selected, option]);
    }
  };

  const handleRemove = (option) => {
    onChange(selected.filter(s => s.id !== option.id));
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [containerRef]);

  const selectedIds = new Set(selected.map(s => s.id));

  return (
    <div style={{ position: 'relative', fontFamily: 'sans-serif', minWidth: 220 }} ref={containerRef}>
      <div 
        style={{
          border: '1px solid #ccc',
          borderRadius: '8px',
          padding: '4px',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '6px',
          cursor: 'pointer',
          background: 'white'
        }}
        onClick={() => setIsOpen(!isOpen)}
      >
        {selected.length > 0 ? (
          selected.map(s => (
            <div key={s.id} style={{
              background: '#e0e0e0',
              borderRadius: '16px',
              padding: '4px 10px',
              display: 'flex',
              alignItems: 'center',
              fontSize: '14px'
            }}>
              {s.name}
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemove(s);
                }}
                style={{
                  border: 'none',
                  background: 'none',
                  marginLeft: '8px',
                  cursor: 'pointer',
                  fontSize: '16px',
                  padding: 0,
                  lineHeight: 1,
                  color: '#555'
                }}
              >
                &times;
              </button>
            </div>
          ))
        ) : (
          <span style={{ padding: '4px 6px', color: '#888', fontSize: '14px' }}>{placeholder}</span>
        )}
      </div>
      {isOpen && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          border: '1px solid #ccc',
          borderRadius: '8px',
          background: 'white',
          zIndex: 100,
          maxHeight: '200px',
          overflowY: 'auto',
          marginTop: '4px'
        }}>
          {options.map(option => (
            <div 
              key={option.id}
              onClick={() => handleSelect(option)}
              style={{
                padding: '10px 12px',
                cursor: 'pointer',
                background: selectedIds.has(option.id) ? '#f0f0f0' : 'white',
                fontWeight: selectedIds.has(option.id) ? '500' : 'normal'
              }}
            >
              {option.name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MultiSelect;
