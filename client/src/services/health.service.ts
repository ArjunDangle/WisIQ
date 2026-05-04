import { ENDPOINTS } from "@/constants/config";

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(ENDPOINTS.HEALTH, {
      method: "GET",
      // Short timeout to avoid hanging if the server is down
      signal: AbortSignal.timeout(5000), 
    });
    return response.ok;
  } catch (error) {
    return false;
  }
}
