import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowUp, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  isGenerating: boolean;
}

export function ChatInput({ onSend, isGenerating }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-expand textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    if (value.trim() && !isGenerating) {
      onSend(value);
      setValue("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto p-4">
      <div
        className={cn(
          "relative flex items-end p-2 rounded-2xl border transition-all duration-300",
          "bg-background/80 backdrop-blur-xl shadow-sm hover:shadow-md",
          isGenerating ? "border-border opacity-70" : "border-border hover:border-muted-foreground/30",
          value.length > 0 ? "border-muted-foreground/30 shadow-md" : ""
        )}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask WisIQ about enterprise hardware..."
          disabled={isGenerating}
          rows={1}
          className="w-full max-h-[200px] bg-transparent text-foreground placeholder:text-muted-foreground resize-none focus:outline-none p-3 pb-2 text-[15px] leading-relaxed disabled:cursor-not-allowed"
        />
        
        <div className="absolute right-3 bottom-3 flex items-center justify-center">
          <AnimatePresence mode="wait">
            {isGenerating ? (
              <motion.div
                key="generating"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="w-8 h-8 flex items-center justify-center rounded-full bg-muted text-muted-foreground"
              >
                <Loader2 className="w-4 h-4 animate-spin" />
              </motion.div>
            ) : (
              <motion.button
                key="send"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                onClick={handleSend}
                disabled={!value.trim()}
                className={cn(
                  "w-8 h-8 flex items-center justify-center rounded-full transition-colors",
                  value.trim() 
                    ? "bg-foreground text-background hover:bg-foreground/90" 
                    : "bg-muted text-muted-foreground cursor-not-allowed"
                )}
              >
                <ArrowUp className="w-4 h-4" strokeWidth={3} />
              </motion.button>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
