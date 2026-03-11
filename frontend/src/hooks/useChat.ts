import { useState, useEffect } from 'react';
import { ChatMessage, ChatResponse } from '@/types/chatbot';
import { ChatbotService } from '@/services/chatbot.service';
import { useAppContext } from '@/context/app-context';

export const useChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Create a session ID state. Initialize it lazily.
  const [sessionId, setSessionId] = useState<string>('');
  const { professionalId } = useAppContext();

  // Generate the session ID only once when the hook first mounts
  useEffect(() => {
    // browser-native UUID generation
    setSessionId(crypto.randomUUID());
  }, []);

  const sendMessage = async (content: string) => {
    const userMessage: ChatMessage = { role: 'user', content };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response: ChatResponse = await ChatbotService.sendMessage({
        message: content,
        professional_id: professionalId,
        session_id: sessionId, // <-- Pass the session ID here
        // Note: You can now remove 'history: messages' if your backend 
        // is handling the memory via Supabase as discussed earlier.
        // For safety, I'll leave it here in case your backend still expects it.
        history: messages, 
      });

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.reply,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      return response;
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  // Allow the UI to trigger a hard reset of the conversation memory
  const startNewChat = () => {
    setSessionId(crypto.randomUUID()); // Generate a fresh session ID
    setMessages([
      {
        role: 'assistant',
        content: 'How can I help you today?',
      },
    ]);
    setError(null);
  };

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    setMessages,
    startNewChat, // <-- Expose this to the UI
  };
};