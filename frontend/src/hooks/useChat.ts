import { useState } from 'react';
import { ChatMessage, ChatResponse } from '@/types/chatbot';
import { ChatbotService } from '@/services/chatbot.service';
import { useAppContext } from '@/context/app-context';

export const useChat = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError]         = useState<string | null>(null);

  // sessionId and messages now live in AppContext so they survive
  // Next.js page navigation without being reset.
  const { professionalId, sessionId, messages, setMessages } = useAppContext();

  const sendMessage = async (content: string) => {
    const userMessage: ChatMessage = { role: 'user', content };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response: ChatResponse = await ChatbotService.sendMessage({
        message: content,
        professional_id: professionalId,
        session_id: sessionId,
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

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    setMessages,
  };
};