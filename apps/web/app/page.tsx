'use client';

import { useState } from 'react';
import { Send, Bot, User, FileText } from 'lucide-react';

interface Source {
  filename: string;
  score: number;
  text: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

export default function Home() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!response.ok) throw new Error('Failed to send message');

      const data = await response.json();
      setMessages((prev) => [
        ...prev,
        { 
          role: 'assistant', 
          content: data.response,
          sources: data.sources 
        },
      ]);
    } catch (error) {
      console.error('Error:', error);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong.' },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center bg-gray-50 p-4">
      <div className="w-full max-w-2xl bg-white rounded-lg shadow-md overflow-hidden flex flex-col h-[80vh]">
        {/* Header */}
        <div className="p-4 border-b bg-white">
          <h1 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
            <Bot className="w-6 h-6 text-blue-600" />
            NoteWise AI
          </h1>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.length === 0 && (
            <div className="text-center text-gray-400 mt-10">
              <p>Start a conversation with your notes.</p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className="flex flex-col gap-2">
              {/* Message Bubble */}
              <div
                className={`flex gap-3 ${
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-5 h-5 text-blue-600" />
                  </div>
                )}
                <div
                  className={`max-w-[85%] rounded-lg p-3 text-sm whitespace-pre-wrap ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {msg.content}
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 text-gray-600" />
                  </div>
                )}
              </div>

              {/* Sources Section (Only for assistant) */}
              {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                <div className="ml-11 max-w-[85%]">
                  <p className="text-xs font-semibold text-gray-500 mb-1 flex items-center gap-1">
                    <FileText className="w-3 h-3" />
                    Sources
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {msg.sources.map((source, sIdx) => (
                      <div 
                        key={sIdx} 
                        className="bg-white border border-gray-200 rounded p-2 text-xs hover:border-blue-300 transition-colors cursor-pointer group"
                        title={source.text}
                      >
                        <div className="font-medium text-gray-700 truncate">
                          {source.filename}
                        </div>
                        <div className="text-gray-400 mt-1 text-[10px]">
                          Relevance: {(source.score * 100).toFixed(0)}%
                        </div>
                        <div className="text-gray-500 mt-1 line-clamp-2 text-[10px] italic group-hover:text-gray-700">
                          "{source.text}"
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
          
          {isLoading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                <Bot className="w-5 h-5 text-blue-600" />
              </div>
              <div className="bg-gray-100 rounded-lg p-3 text-sm text-gray-500 animate-pulse">
                Thinking...
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t bg-white">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your notes..."
              className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}
