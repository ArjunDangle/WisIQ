import { useState, useEffect } from "react";
import { checkHealth } from "@/services/health.service";

export function useHealthCheck(intervalMs = 30000) {
  const [isOnline, setIsOnline] = useState<boolean>(true); // Optimistically start true

  useEffect(() => {
    let mounted = true;

    const performCheck = async () => {
      const status = await checkHealth();
      if (mounted) {
        setIsOnline(status);
      }
    };

    // Initial check
    performCheck();

    // Poll every X ms
    const intervalId = setInterval(performCheck, intervalMs);

    return () => {
      mounted = false;
      clearInterval(intervalId);
    };
  }, [intervalMs]);

  return isOnline;
}
