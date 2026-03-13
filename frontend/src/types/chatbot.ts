export type Role = 'user' | 'assistant';

export interface ChatMessage {
  role: Role;
  content: string;
  metadata?: ChatMetadata; // carried alongside the message for rendering
}

export interface ChatRequest {
  message: string;
  professional_id: string;
  session_id: string;
  history?: ChatMessage[];
}

// ---------------------------------------------------------------------------
// Display payload — mirrors backend schemas/chatbot.py DisplayPayload
// ---------------------------------------------------------------------------

export type DisplayType =
  | 'day_schedule'
  | 'booking_list'
  | 'slot_created'
  | 'slot_deleted'
  | 'booking_created'
  | 'booking_cancelled'
  | 'client_search';

export interface SlotDisplayItem {
  slot_id: string;
  date: string;
  start_time: string;
  end_time: string;
  status: string;
}

export interface BookingDisplayItem {
  booking_id: string;
  slot_id: string;
  client_id: string;
  client_name?: string;
  date: string;
  start_time: string;
  end_time: string;
  note?: string;
  status?: string;
}

export interface ClientSearchItem {
  client_id: string;
  name: string;
}

export interface DisplayPayload {
  type: DisplayType;
  items?: (SlotDisplayItem | BookingDisplayItem | ClientSearchItem | Record<string, unknown>)[];
  item?: Record<string, unknown>;
}

export interface ChatMetadata {
  last_action?: string;
  parameters?: Record<string, unknown>;
  display?: DisplayPayload;
}

export interface ChatResponse {
  reply: string;
  intent?: string;
  action_suggested?: boolean;
  metadata?: ChatMetadata;
}