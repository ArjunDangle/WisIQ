"use client";

import { useEffect, useRef } from "react";
import { useChatStore } from "@/store/chat.store";
import { useChatStream } from "@/hooks/useChatStream";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { motion, AnimatePresence } from "framer-motion";

export function ChatContainer() {
  const { messages, isTyping, initializeSession } = useChatStore();
  const { sendMessage } = useChatStream();
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize session on mount
  useEffect(() => {
    initializeSession();
  }, [initializeSession]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  return (
    <div className="flex flex-col h-full w-full max-w-4xl mx-auto overflow-hidden">
      <div 
        ref={containerRef}
        className="flex-1 overflow-y-auto px-4 pt-10 pb-4 scroll-smooth no-scrollbar"
      >
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center opacity-70">
            <h1 className="text-3xl font-light tracking-tight mb-3">WisIQ</h1>
            <p className="text-muted-foreground text-sm max-w-md">
              Your enterprise hardware AI assistant. Ask me anything about module configurations, AT commands, or datasheets.
            </p>
          </div>
        ) : (
          <div className="flex flex-col min-h-full justify-end">
            <AnimatePresence initial={false}>
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
            </AnimatePresence>
            <div ref={bottomRef} className="h-2 w-full" />
          </div>
        )}
      </div>

      <div className="w-full shrink-0 pb-6 pt-2 bg-gradient-to-t from-background via-background to-transparent">
        <ChatInput onSend={sendMessage} isGenerating={isTyping} />
      </div>
    </div>
  );
}
