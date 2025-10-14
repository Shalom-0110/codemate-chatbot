import React, { useState } from 'react';

export default function InputBox({ onSend }) {
  const [input, setInput] = useState('');

  const send = () => {
    if (!input.trim()) return;
    onSend(input);
    setInput('');
  };

  const handleKey = (e) => {
    if (e.key === 'Enter') send();
  };

  return (
    <div className="input-box">
      <input
        type="text"
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyDown={handleKey}
        placeholder="Ask me a coding question..."
      />
      <button onClick={send}>Send</button>
    </div>
  );
}
