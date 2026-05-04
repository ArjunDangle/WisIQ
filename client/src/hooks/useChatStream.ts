import { useRef } from "react";
import { useChatStore } from "@/store/chat.store";
import { streamChatQuery } from "@/services/chat.service";
import { ChatSSEEvent } from "@/types/api.types";
import { generateUUID } from "@/lib/utils";

export function useChatStream() {
  const { sessionId, addMessage, updateMessage, setTyping } = useChatStore();
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = async (content: string) => {
    if (!sessionId || !content.trim()) return;

    // Cancel any ongoing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    // Add user message
    const userMessageId = generateUUID();
    addMessage({
      id: userMessageId,
      role: "user",
      content,
    });

    // Create placeholder for AI message
    const aiMessageId = generateUUID();
    addMessage({
      id: aiMessageId,
      role: "assistant",
      content: "",
      isStreaming: true,
    });

    setTyping(true);

    try {
      const response = await streamChatQuery(
        { session_id: sessionId, message: content },
        abortControllerRef.current.signal
      );

      if (!response.ok || !response.body) {
        throw new Error("Failed to connect to the stream.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let done = false;

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;

        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const dataStr = line.replace("data: ", "").trim();
              if (!dataStr) continue;

              try {
                const event: ChatSSEEvent = JSON.parse(dataStr);
                const currentMsg = useChatStore.getState().messages.find((m) => m.id === aiMessageId);

                switch (event.type) {
                  case "metadata":
                    updateMessage(aiMessageId, {
                      intent: event.intent_detected,
                      hardware: event.hardware_detected,
                    });
                    break;
                  case "token":
                    if (currentMsg) {
                      updateMessage(aiMessageId, {
                        content: currentMsg.content + event.content,
                      });
                    }
                    break;
                  case "end":
                    updateMessage(aiMessageId, { isStreaming: false });
                    setTyping(false);
                    break;
                  case "error":
                    updateMessage(aiMessageId, { 
                      isStreaming: false, 
                      isError: true,
                      content: (currentMsg?.content || "") + "\n\nError: " + event.message 
                    });
                    setTyping(false);
                    break;
                }
              } catch (e) {
                console.error("Error parsing SSE event JSON", e, dataStr);
              }
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name === "AbortError") {
        console.log("Stream aborted");
      } else {
        console.error("Stream error:", error);
        updateMessage(aiMessageId, { 
          isStreaming: false, 
          isError: true,
          content: "Connection failed. Please try again." 
        });
      }
      setTyping(false);
    }
  };

  const stopStream = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  return { sendMessage, stopStream };
}
