'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useChat } from '@/hooks/useChat';
import { useAppContext } from '@/context/app-context';
import {
  DisplayPayload,
  SlotDisplayItem,
  BookingDisplayItem,
  ClientSearchItem,
} from '@/types/chatbot';


// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const fmt12 = (t: string) => {
  if (!t) return '';
  const [h, m] = t.split(':').map(Number);
  const ampm = h >= 12 ? 'PM' : 'AM';
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${ampm}`;
};

const fmtDate = (d: string) => {
  if (!d) return '';
  const [y, mo, day] = d.split('-');
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return `${months[Number(mo) - 1]} ${Number(day)}, ${y}`;
};

const statusColor = (s = '') => {
  const st = s.toLowerCase();
  if (st === 'available')  return 'bg-emerald-50 text-emerald-700';
  if (st === 'booked')     return 'bg-blue-50 text-blue-700';
  if (st === 'cancelled')  return 'bg-red-50 text-red-700';
  if (st === 'scheduled')  return 'bg-indigo-50 text-indigo-700';
  if (st === 'completed')  return 'bg-gray-100 text-gray-600';
  return 'bg-gray-100 text-gray-600';
};



// ---------------------------------------------------------------------------
// Card components
// ---------------------------------------------------------------------------

const SlotCard: React.FC<{ item: SlotDisplayItem; onAction: (msg: string) => void }> = ({ item, onAction }) => (
  <div className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden">
    <div className="px-5 py-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-gray-800">
          {fmt12(item.start_time)} – {fmt12(item.end_time)}
        </span>
        <span className={`text-[10px] font-bold uppercase tracking-wide px-2.5 py-1 rounded-full ${statusColor(item.status)}`}>
          {item.status}
        </span>
      </div>
      <p className="text-xs text-gray-400 mt-1">{fmtDate(item.date)}</p>
    </div>
    {item.status === 'available' && (
      <div className="border-t border-gray-50 px-5 py-3 flex gap-4">
        <button
          onClick={() => onAction(`Delete slot ${item.slot_id}`)}
          className="text-xs font-semibold text-red-500 hover:text-red-700 transition-colors"
        >
          Delete Slot
        </button>
      </div>
    )}
  </div>
);

const BookingCard: React.FC<{ item: BookingDisplayItem; onAction: (msg: string) => void }> = ({ item, onAction }) => {
  // client_name is flattened by the backend ResponseBuilder from the Supabase join.
  // No async fetch needed.
  const clientName = item.client_name ?? '';

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden">
      <div className="px-5 py-4">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-sm font-semibold text-gray-800">
              {clientName || 'Unknown Client'}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">
              {fmt12(item.start_time)} – {fmt12(item.end_time)}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">{fmtDate(item.date)}</p>
          </div>
          <span className={`text-[10px] font-bold uppercase tracking-wide px-2.5 py-1 rounded-full shrink-0 ${statusColor(item.status)}`}>
            {item.status ?? 'scheduled'}
          </span>
        </div>
        {item.note && (
          <p className="mt-2 text-xs text-gray-400 italic truncate">"{item.note}"</p>
        )}
      </div>
      <div className="border-t border-gray-50 px-5 py-3 flex gap-4">
        <button
          onClick={() => onAction(`Cancel booking ${item.booking_id}`)}
          className="text-xs font-semibold text-red-500 hover:text-red-700 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};

const ConfirmationCard: React.FC<{ type: 'success' | 'delete'; title: string; subtitle?: string }> = ({ type, title, subtitle }) => (
  <div className={`rounded-2xl border px-5 py-4 flex items-start gap-3 ${type === 'success' ? 'bg-emerald-50 border-emerald-100' : 'bg-red-50 border-red-100'}`}>
    <span className="text-lg">{type === 'success' ? '✅' : '🗑️'}</span>
    <div>
      <p className={`text-sm font-semibold ${type === 'success' ? 'text-emerald-800' : 'text-red-800'}`}>{title}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
    </div>
  </div>
);

const ClientSearchCard: React.FC<{ items: ClientSearchItem[]; onSelect: (msg: string) => void }> = ({ items, onSelect }) => (
  <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
    <div className="px-5 py-3 border-b border-gray-50">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Multiple clients found</p>
    </div>
    <div className="divide-y divide-gray-50">
      {items.map((c) => (
        <button
          key={c.client_id}
          onClick={() => onSelect(`Use client ${c.client_id} — ${c.name}`)}
          className="w-full text-left px-5 py-3 hover:bg-gray-50 transition-colors"
        >
          <p className="text-sm font-medium text-gray-800">{c.name}</p>
          <p className="text-[10px] text-gray-400 font-mono mt-0.5">{c.client_id}</p>
        </button>
      ))}
    </div>
  </div>
);

// ---------------------------------------------------------------------------
// Main display renderer — reads metadata.display, never parses reply string
// ---------------------------------------------------------------------------

const DisplayRenderer: React.FC<{ display: DisplayPayload; onAction: (msg: string) => void }> = ({ display, onAction }) => {
  const { type, items = [], item } = display;

  if (type === 'day_schedule') {
    const slots = items as SlotDisplayItem[];
    if (!slots.length) return <p className="text-xs text-gray-400 italic ml-1">No slots found for this date.</p>;
    return (
      <div className="grid grid-cols-1 gap-3 mt-3">
        {slots.map((s) => <SlotCard key={s.slot_id} item={s} onAction={onAction} />)}
      </div>
    );
  }

  if (type === 'booking_list') {
    const bookings = items as BookingDisplayItem[];
    if (!bookings.length) return <p className="text-xs text-gray-400 italic ml-1">No upcoming bookings.</p>;
    return (
      <div className="grid grid-cols-1 gap-3 mt-3">
        {bookings.map((b) => <BookingCard key={b.booking_id} item={b} onAction={onAction} />)}
      </div>
    );
  }

  if (type === 'booking_created') {
    const b = item as BookingDisplayItem | undefined;
    return (
      <div className="mt-3">
        <ConfirmationCard
          type="success"
          title="Booking confirmed"
          subtitle={b ? `${fmtDate(b.date ?? '')}  •  ${fmt12(b.start_time ?? '')} – ${fmt12(b.end_time ?? '')}` : undefined}
        />
      </div>
    );
  }

  if (type === 'slot_created') {
    const s = item as SlotDisplayItem | undefined;
    return (
      <div className="mt-3">
        <ConfirmationCard
          type="success"
          title="Slot opened"
          subtitle={s ? `${fmtDate(s.date ?? '')}  •  ${fmt12(s.start_time ?? '')} – ${fmt12(s.end_time ?? '')}` : undefined}
        />
      </div>
    );
  }

  if (type === 'booking_cancelled') {
    return <div className="mt-3"><ConfirmationCard type="delete" title="Booking cancelled" /></div>;
  }

  if (type === 'slot_deleted') {
    return <div className="mt-3"><ConfirmationCard type="delete" title="Slot removed" /></div>;
  }

  if (type === 'client_search') {
    const clients = items as ClientSearchItem[];
    return (
      <div className="mt-3">
        <ClientSearchCard items={clients} onSelect={onAction} />
      </div>
    );
  }

  return null;
};

// ---------------------------------------------------------------------------
// Inline text renderer — bold (**) and code (`) only
// ---------------------------------------------------------------------------

const renderText = (text: string, baseKey: string) => {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, index) => {
    const key = `${baseKey}-${index}`;
    if (part.startsWith('**') && part.endsWith('**'))
      return <strong key={key} className="font-semibold text-gray-900">{part.slice(2, -2)}</strong>;
    if (part.startsWith('`') && part.endsWith('`'))
      return <code key={key} className="bg-gray-100 px-1.5 py-0.5 rounded text-blue-600 font-mono text-xs border border-gray-200">{part.slice(1, -1)}</code>;
    return part;
  });
};

// ---------------------------------------------------------------------------
// ChatInterface
// ---------------------------------------------------------------------------

export const ChatInterface: React.FC = () => {
  const { messages, isLoading, error, sendMessage, setMessages } = useChat();
  const { professionalName, resetSession } = useAppContext();

  const [input, setInput]             = useState('');
  const [showConfirm, setShowConfirm] = useState(false);
  const messagesEndRef                = useRef<HTMLDivElement>(null);
  const inputRef                      = useRef<HTMLInputElement>(null);

  const getInitials = (name: string) =>
    name.split(' ').map((n) => n[0]).join('').toUpperCase();

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, isLoading]);
  useEffect(() => { inputRef.current?.focus(); }, []);
  useEffect(() => { if (!isLoading) inputRef.current?.focus(); }, [messages, isLoading]);

  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{ role: 'assistant', content: 'How can I help you today?' }]);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    const currentInput = input;
    setInput('');
    inputRef.current?.focus();
    await sendMessage(currentInput);
  };

  const handleAction = useCallback((msg: string) => { sendMessage(msg); }, [sendMessage]);

  const handleConfirmNewChat = () => { setShowConfirm(false); resetSession(); };

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
      options: ["View today's schedule", 'View schedule by date', 'View schedule by client', 'View upcoming bookings'],
    },
  ];

  return (
    <div
      className="flex flex-col h-[calc(100vh-64px)] bg-white max-w-5xl mx-auto w-full px-6 py-2 relative"
      onClick={() => inputRef.current?.focus()}
    >
      {/* Confirmation Modal */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl p-6 max-w-sm w-full mx-4">
            <h3 className="text-base font-semibold text-gray-900 mb-2">Start a new chat?</h3>
            <p className="text-sm text-gray-500 mb-6">
              This action will permanently delete the chat history. This cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setShowConfirm(false)} className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
                Cancel
              </button>
              <button onClick={handleConfirmNewChat} className="px-4 py-2 text-sm font-medium text-white bg-red-500 hover:bg-red-600 rounded-lg transition-colors">
                Proceed
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-center px-4 pb-2 border-b border-gray-100 mb-2">
        <div className="flex items-center space-x-2">
          <div className="w-1 h-5 bg-green-500 rounded-full" />
          <h2 className="text-lg font-semibold text-gray-800 tracking-tight">Mirror Assistant</h2>
        </div>
        <button
          onClick={() => setShowConfirm(true)}
          className="text-sm text-gray-500 hover:text-blue-600 font-medium px-3 py-1 rounded-md hover:bg-blue-50 transition-colors"
        >
          + New Chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 px-4">
        {messages.map((msg, index) => (
          <div key={index} className="flex flex-col">
            <div className={`flex items-start space-x-3 ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-green-500 text-white'
              }`}>
                {msg.role === 'user' ? getInitials(professionalName) : 'M'}
              </div>

              <div className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
                msg.role === 'user' ? 'bg-gray-100 text-gray-800' : 'text-gray-800'
              }`}>
                {/* Plain-text reply — bold and inline-code only, zero HTML parsing */}
                <p>{renderText(msg.content, `msg-${index}`)}</p>

                {/* Structured display — driven by metadata.display, never by reply content */}
                {msg.role === 'assistant' && msg.metadata?.display && (
                  <DisplayRenderer display={msg.metadata.display} onAction={handleAction} />
                )}
              </div>
            </div>

            {/* Quick-action menu on the first greeting only */}
            {msg.role === 'assistant' && index === 0 && (
              <div className="ml-11 mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl">
                {menuOptions.map((section) => (
                  <div key={section.title} className="bg-gray-50 rounded-xl p-4 border border-gray-100 shadow-sm">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase mb-3 px-1">{section.title}</h3>
                    <div className="space-y-2">
                      {section.options.map((option) => (
                        <button
                          key={option}
                          onClick={() => sendMessage(option)}
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
            <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600 text-xs font-bold">M</div>
            <div className="flex space-x-1.5 py-4 px-1">
              <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-bounce" />
              <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-bounce delay-75" />
              <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-bounce delay-150" />
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

      {/* Input */}
      <div className="p-3 border-t border-gray-100 mt-2">
        <form onSubmit={handleSubmit} className="flex items-center space-x-3 bg-white rounded-xl px-4 py-1.5 border border-gray-200 focus-within:ring-2 focus-within:ring-blue-100 focus-within:bg-white transition-all">
          <button type="button" className="text-gray-400 hover:text-gray-600">🎤</button>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Write message"
            className="flex-1 bg-white text-black border-none focus:ring-0 text-sm py-2 outline-none"
          />
          <div className="flex items-center space-x-3">
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="bg-green-600 hover:bg-green-700 text-white px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center space-x-2 transition-all hover:shadow-lg hover:shadow-green-100 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:shadow-none disabled:scale-100"
            >
              <span>Send</span>
              <span>✈️</span>
            </button>
          </div>
        </form>
        <div className="mt-4 flex flex-col items-center">
          <div className="w-full h-[1px] bg-gray-100 mb-2" />
          <p className="text-[10px] text-gray-400 italic tracking-tight">
            Assistant can make mistakes. Please cross-check important information.
          </p>
        </div>
      </div>
    </div>
  );
};