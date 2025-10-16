import React from 'react';
import './MessageBubble.css';

export default function MessageBubble({ text, sender }) {
  return (
    <div className={`message-bubble ${sender}`}>
      {text.split('\n').map((line, i) => (
        <p key={i}>{line}</p>
      ))}
    </div>
  );
}
