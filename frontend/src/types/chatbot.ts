export type Role = 'user' | 'assistant';

export interface ChatMessage {
  role: Role;
  content: string;
}

export interface ChatRequest {
  message: string;
  professional_id: string;
  session_id: string;
  history?: ChatMessage[];
}

export interface ChatResponse {
  reply: string;
  intent?: string;
  action_suggested?: boolean;
}
