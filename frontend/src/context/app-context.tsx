
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

  // Initialise with default values to match Server-Side Rendering (SSR).
  // This prevents hydration mismatches because the first client render will match the server.
  const [sessionId, setSessionId] = useState<string>('');
  const [messages, setMessages]   = useState<ChatMessage[]>([INITIAL_MESSAGE]);
  const [isLoaded, setIsLoaded]   = useState(false);

  // Load from sessionStorage only AFTER mount
  useEffect(() => {
    const storedId = sessionStorage.getItem(SESSION_ID_KEY);
    const storedMsg = sessionStorage.getItem(MESSAGES_KEY);

    if (storedId) {
      setSessionId(storedId);
    } else {
      const newId = generateUUID();
      setSessionId(newId);
      sessionStorage.setItem(SESSION_ID_KEY, newId);
    }

    if (storedMsg) {
      try {
        setMessages(JSON.parse(storedMsg));
      } catch (err) {
        console.error('Failed to parse stored messages', err);
      }
    }
    setIsLoaded(true);
  }, []);

  // Keep sessionStorage in sync whenever sessionId or messages change, 
  // but only after we've finished the initial load.
  useEffect(() => {
    if (isLoaded) {
      sessionStorage.setItem(SESSION_ID_KEY, sessionId);
    }
  }, [sessionId, isLoaded]);

  useEffect(() => {
    if (isLoaded) {
      sessionStorage.setItem(MESSAGES_KEY, JSON.stringify(messages));
    }
  }, [messages, isLoaded]);

  // Called after the user confirms "New Chat"
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
