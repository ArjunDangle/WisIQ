import { ChatContainer } from "@/components/features/chat/ChatContainer";

export default function Home() {
  return (
    <div className="flex-1 w-full flex flex-col items-center justify-center relative">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-muted/50 via-background to-background pointer-events-none" />
      <div className="relative w-full h-full z-10 flex flex-col">
        <ChatContainer />
      </div>
    </div>
  );
}
