import { create } from "zustand";
import { ChatState, Message } from "@/types/chat.types";
import { generateUUID } from "@/lib/utils";

export const useChatStore = create<ChatState>((set) => ({
  sessionId: null,
  messages: [],
  isTyping: false,
  
  initializeSession: () => {
    set((state) => {
      if (!state.sessionId) {
        return { sessionId: generateUUID() };
      }
      return state;
    });
  },
  
  addMessage: (message: Message) => {
    set((state) => ({
      messages: [...state.messages, message],
    }));
  },
  
  updateMessage: (id: string, updates: Partial<Message>) => {
    set((state) => ({
      messages: state.messages.map((msg) => 
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    }));
  },
  
  setTyping: (isTyping: boolean) => {
    set({ isTyping });
  },
  
  clearChat: () => {
    set({ messages: [], isTyping: false });
  },
}));
