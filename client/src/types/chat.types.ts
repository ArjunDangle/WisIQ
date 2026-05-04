export type Role = "user" | "assistant";

export interface Message {
  id: string;
  role: Role;
  content: string;
  intent?: string;
  hardware?: string[];
  isStreaming?: boolean;
  isError?: boolean;
}

export interface ChatState {
  sessionId: string | null;
  messages: Message[];
  isTyping: boolean;
  initializeSession: () => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  setTyping: (isTyping: boolean) => void;
  clearChat: () => void;
}
