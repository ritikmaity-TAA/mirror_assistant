'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '@/hooks/useChat';
import { useAppContext } from '@/context/app-context';

export const ChatInterface: React.FC = () => {
  const { messages, isLoading, error, sendMessage, setMessages } = useChat();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { professionalName } = useAppContext();

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase();
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Initial greeting
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          role: 'assistant',
          content: 'How can I help you today?',
        },
      ]);
    }
  }, [setMessages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const currentInput = input;
    setInput('');
    await sendMessage(currentInput);
  };

  const menuOptions = [
    {
      title: 'Manage Booking Slots',
      options: ['Open booking slot', 'Edit booking slot', 'Delete booking slot'],
    },
    {
      title: 'Manage Bookings',
      options: ['Create booking', 'Edit booking', 'Delete booking'],
    },
    {
      title: 'View Schedule',
      options: [
        "View today's schedule",
        'View schedule by date',
        'View schedule by client',
        'View upcoming bookings',
      ],
    },
  ];

  const handleMenuClick = (option: string) => {
    sendMessage(option);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] bg-white max-w-5xl mx-auto w-full p-6">
      <div className="flex-1 overflow-y-auto space-y-6 px-4">
        {messages.map((msg, index) => (
          <div key={index} className="flex flex-col">
            <div className={`flex items-start space-x-3 ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-green-500 text-white'
                }`}>
                {msg.role === 'user' ? getInitials(professionalName) : 'M'}
              </div>
              <div className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${msg.role === 'user' ? 'bg-gray-100 text-gray-800' : 'text-gray-800'
                }`}>
                {msg.content}
              </div>
            </div>

            {/* Menu Options (Only for initial assistant message or when relevant) */}
            {msg.role === 'assistant' && index === 0 && (
              <div className="ml-11 mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl">
                {menuOptions.map((section) => (
                  <div key={section.title} className="bg-gray-50 rounded-xl p-4 border border-gray-100 shadow-sm">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase mb-3 px-1">{section.title}</h3>
                    <div className="space-y-2">
                      {section.options.map((option) => (
                        <button
                          key={option}
                          onClick={() => handleMenuClick(option)}
                          className="w-full text-left text-sm text-gray-700 bg-white hover:bg-gray-100 px-3 py-2 rounded-lg border border-gray-200 transition-colors shadow-sm"
                        >
                          {option}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center text-white text-xs font-bold">M</div>
            <div className="flex space-x-1 py-3">
              <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce delay-75"></div>
              <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce delay-150"></div>
            </div>
          </div>
        )}

        {error && (
          <div className="flex justify-center py-4">
            <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg text-xs border border-red-100 shadow-sm">
              Error: {error}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Section */}
      <div className="p-4 border-t border-gray-100">
        <form onSubmit={handleSubmit} className="flex items-center space-x-3 bg-white rounded-xl px-4 py-2 border border-gray-200 focus-within:ring-2 focus-within:ring-blue-100 focus-within:bg-white transition-all">
          <button type="button" className="text-gray-400 hover:text-gray-600">
            🎤
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            placeholder="Write message"
            className="flex-1 bg-white text-black border-none focus:ring-0 text-sm py-2 outline-none"
          />
          <div className="flex items-center space-x-3">
            <button type="button" className="text-gray-400 hover:text-gray-600 text-lg">📎</button>
            <button type="button" className="text-gray-400 hover:text-gray-600 text-lg">🖼️</button>
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center space-x-2 transition-colors disabled:opacity-50"
            >
              <span>Send</span>
              <span>✈️</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
