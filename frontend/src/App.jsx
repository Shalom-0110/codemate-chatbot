import React, { useState } from 'react';
import MessageBubble from './components/MessageBubble';
import InputBox from './components/InputBox';
import axios from 'axios';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

export default function App() {
  const [messages, setMessages] = useState([]);

  const sendMessage = async (msg) => {
    setMessages([...messages, { sender: 'user', text: msg }]);
    try {
      const res = await axios.post('http://127.0.0.1:8000/ask/', { question: msg });
      setMessages(prev => [...prev, { sender: 'bot', text: res.data.result }]);
    } catch (err) {
      toast.error("Error fetching answer!");
      setMessages(prev => [...prev, { sender: 'bot', text: 'Error fetching answer' }]);
    }
  };

  return (
    <div className="chat-container">
      {messages.map((msg, idx) => (
        <MessageBubble key={idx} text={msg.text} sender={msg.sender} />
      ))}
      <InputBox onSend={sendMessage} />
      <ToastContainer position="top-right" autoClose={3000} />
    </div>
  );
}
