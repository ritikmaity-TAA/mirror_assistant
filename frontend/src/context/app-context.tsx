// app context
'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { DEFAULT_PROFESSIONAL_ID } from '@/lib/constants';
import { ChatMessage } from '@/types/chatbot';

// Keys for sessionStorage — sessionStorage is cleared automatically when the
// browser tab/window is closed, satisfying the "app closed = session expired" rule.
const SESSION_ID_KEY = 'mirror_session_id';
const MESSAGES_KEY   = 'mirror_messages';

const generateUUID = (): string => {
  if (typeof window !== 'undefined' && window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
};

const INITIAL_MESSAGE: ChatMessage = {
  role: 'assistant',
  content: 'How can I help you today?',
};

interface AppContextType {
  // Professional
  professionalId: string;
  setProfessionalId: (id: string) => void;
  professionalName: string;
  setProfessionalName: (name: string) => void;
  professionalRole: string;
  setProfessionalRole: (role: string) => void;

  // Chat session — lifted here so they survive page navigation
  sessionId: string;
  messages: ChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  resetSession: () => void; // called by "New Chat" after confirmation
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [professionalId, setProfessionalId] = useState(DEFAULT_PROFESSIONAL_ID);
  const [professionalName, setProfessionalName] = useState('Shreya Jain');
  const [professionalRole, setProfessionalRole] = useState('Psychologist');

  // Initialise sessionId from sessionStorage, or generate a fresh one.
  // This persists across Next.js soft navigations but clears on tab close.
  const [sessionId, setSessionId] = useState<string>(() => {
    if (typeof window === 'undefined') return generateUUID();
    return sessionStorage.getItem(SESSION_ID_KEY) ?? generateUUID();
  });

  // Initialise messages from sessionStorage so the chat survives navigation.
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    if (typeof window === 'undefined') return [INITIAL_MESSAGE];
    try {
      const stored = sessionStorage.getItem(MESSAGES_KEY);
      return stored ? JSON.parse(stored) : [INITIAL_MESSAGE];
    } catch {
      return [INITIAL_MESSAGE];
    }
  });

  // Keep sessionStorage in sync whenever sessionId or messages change.
  useEffect(() => {
    sessionStorage.setItem(SESSION_ID_KEY, sessionId);
  }, [sessionId]);

  useEffect(() => {
    sessionStorage.setItem(MESSAGES_KEY, JSON.stringify(messages));
  }, [messages]);

  // Called after the user confirms "New Chat" — generates a fresh session
  // and clears both in-memory state and sessionStorage.
  const resetSession = () => {
    const newId = generateUUID();
    setSessionId(newId);
    setMessages([INITIAL_MESSAGE]);
    sessionStorage.setItem(SESSION_ID_KEY, newId);
    sessionStorage.setItem(MESSAGES_KEY, JSON.stringify([INITIAL_MESSAGE]));
  };

  return (
    <AppContext.Provider
      value={{
        professionalId,
        setProfessionalId,
        professionalName,
        setProfessionalName,
        professionalRole,
        setProfessionalRole,
        sessionId,
        messages,
        setMessages,
        resetSession,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};