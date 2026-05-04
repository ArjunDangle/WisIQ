export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const ENDPOINTS = {
  HEALTH: `${API_URL}/health`,
  CHAT_QUERY: `${API_URL}/chat/query`,
};
