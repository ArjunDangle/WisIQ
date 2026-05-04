import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/cjs/styles/prism";
import { Message } from "@/types/chat.types";
import { HardwareBadge } from "./HardwareBadge";
import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("flex w-full mb-6", isUser ? "justify-end" : "justify-start")}
    >
      <div className={cn("max-w-[85%] md:max-w-[75%] flex flex-col")}>
        {!isUser && (
          <HardwareBadge intent={message.intent} hardware={message.hardware} />
        )}

        <div
          className={cn(
            "px-5 py-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap break-words shadow-sm transition-colors duration-300",
            isUser
              ? "bg-foreground text-background rounded-tr-sm"
              : "bg-muted text-foreground rounded-tl-sm border border-border/50",
            message.isError && !isUser && "bg-accent-amber-bg text-accent-amber border-accent-amber/30"
          )}
        >
          {isUser ? (
            message.content
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, inline, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || "");
                    return !inline && match ? (
                      <div className="my-4 rounded-lg overflow-hidden border border-border">
                        <SyntaxHighlighter
                          {...props}
                          style={oneDark}
                          language={match[1]}
                          PreTag="div"
                          customStyle={{ margin: 0, padding: "1rem", backgroundColor: "#000" }}
                        >
                          {String(children).replace(/\n$/, "")}
                        </SyntaxHighlighter>
                      </div>
                    ) : (
                      <code {...props} className="bg-muted-foreground/20 px-1.5 py-0.5 rounded-md text-xs font-mono">
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
              {message.isStreaming && (
                <motion.span
                  animate={{ opacity: [0, 1, 0] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                  className="inline-block w-2 h-4 ml-1 bg-foreground align-middle"
                />
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
