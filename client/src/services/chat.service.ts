import { ENDPOINTS } from "@/constants/config";
import { ChatQueryPayload } from "@/types/api.types";

export async function streamChatQuery(
  payload: ChatQueryPayload,
  signal?: AbortSignal
): Promise<Response> {
  return fetch(ENDPOINTS.CHAT_QUERY, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "text/event-stream",
    },
    body: JSON.stringify(payload),
    signal,
  });
}
