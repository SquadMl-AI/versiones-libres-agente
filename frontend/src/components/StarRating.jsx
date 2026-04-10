import React from "react";

export default function StarRating({ rating, setRating, disabled = false, max = 5 }) {
  return (
    <div style={{ display: "inline-block" }}>
      {[...Array(max)].map((_, i) => (
        <span
          key={i}
          style={{
            cursor: disabled ? "not-allowed" : "pointer",
            color: i < rating ? "#FFD700" : "#ccc",
            fontSize: 28,
            marginRight: 2
          }}
          onClick={() => !disabled && setRating(i + 1)}
          role="button"
          aria-label={`Calificar con ${i + 1} estrellas`}
        >
          ★
        </span>
      ))}
    </div>
  );
}
