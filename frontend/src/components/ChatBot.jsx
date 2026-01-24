import React, { useState } from 'react'
import { Send } from 'lucide-react'

export default function ChatBot() {
  const [messages, setMessages] = useState([
    { type: 'bot', text: 'Hello! I am MaatruRaksha AI. How can I help you today?' }
  ])
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (!input.trim()) return

    // Add user message
    setMessages([...messages, { type: 'user', text: input }])

    // Simulate bot response
    setTimeout(() => {
      setMessages(prev => [...prev, {
        type: 'bot',
        text: 'I have received your message. Our healthcare team will respond shortly.'
      }])
    }, 500)

    setInput('')
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-4 h-96 flex flex-col">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Chat with MaatruRaksha</h3>

      <div className="flex-1 overflow-y-auto mb-4 space-y-3">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`px-4 py-2 rounded-lg max-w-xs ${
                msg.type === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-900'
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type your message..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
        <button
          onClick={handleSend}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}