"use client";

import { useHealthCheck } from "@/hooks/useHealthCheck";
import { cn } from "@/lib/utils";

export function HealthDot() {
  const isOnline = useHealthCheck(30000);

  return (
    <div className="relative flex items-center justify-center w-3 h-3">
      {isOnline && (
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-20"></span>
      )}
      <span
        className={cn(
          "relative inline-flex rounded-full h-2 w-2 transition-colors duration-500",
          isOnline ? "bg-green-500" : "bg-muted-foreground/40"
        )}
      />
    </div>
  );
}
