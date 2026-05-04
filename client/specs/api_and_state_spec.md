# API & State Specification

## Session Management
* On initial load, the client must generate a standard UUID (8-character hex or standard v4) and store it in state or session storage.
* This `session_id` must be passed with every chat request to maintain LangGraph state on the backend.

## 1. Health Polling (`GET /health`)
* **Endpoint:** `http://localhost:8000/health`
* **Behavior:** A lightweight hook (`useHealthCheck`) should ping this endpoint every 30 seconds.
* **UI Integration:** Display a minimalist, tiny glowing dot in the header (Green for online, Red/Gray for offline).

## 2. SSE Streaming Logic (`POST /chat/query`)
* **Endpoint:** `http://localhost:8000/chat/query`
* **Payload:** `{"session_id": "<uuid>", "message": "<user_input>"}`
* **Behavior:** The frontend must use the native `fetch` API and a `TextDecoder` to read the Server-Sent Events stream.

**Expected SSE Event Types (JSON parsed from `data:` lines):**

1.  **Metadata Event (Fires first):**
    ```json
    {"type": "metadata", "intent_detected": "command_lookup", "hardware_detected": ["rak3172"]}
    ```
    *Action:* Update the current AI message state to display these badges immediately.

2.  **Token Event (Fires continuously):**
    ```json
    {"type": "token", "content": "The AT command to join "}
    ```
    *Action:* Append `content` to the current AI message string to create the typewriter effect.

3.  **End Event (Fires last):**
    ```json
    {"type": "end"}
    ```
    *Action:* Terminate the stream, finalize the message block, and re-enable the chat input.

4.  **Error Event:**
    ```json
    {"type": "error", "message": "..."}
    ```
    *Action:* Terminate the stream and display an elegant error boundary or toast notification.