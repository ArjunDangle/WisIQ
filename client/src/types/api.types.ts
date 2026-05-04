export type SSEEventType = "metadata" | "token" | "end" | "error";

export interface MetadataEvent {
  type: "metadata";
  intent_detected?: string;
  hardware_detected?: string[];
}

export interface TokenEvent {
  type: "token";
  content: string;
}

export interface EndEvent {
  type: "end";
}

export interface ErrorEvent {
  type: "error";
  message: string;
}

export type ChatSSEEvent = MetadataEvent | TokenEvent | EndEvent | ErrorEvent;

export interface ChatQueryPayload {
  session_id: string;
  message: string;
}
