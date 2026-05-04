# UI/UX Design System

## Aesthetic Identity
The UI must feel incredibly premium, mirroring an "Apple-esque" or high-end "editorial" aesthetic. Draw inspiration from minimalist fashion apps (like Zara), premium creative agencies, and modern interfaces (like Hinge). 

## Core Visual Rules
* **Clutter-Free:** Extreme minimalism. Remove unnecessary borders, heavy drop shadows, and visual noise.
* **Typography:** Prioritize high-end, highly legible typography. Use refined font weights and ample line height. 
* **Color Palette:** Monochromatic base (pure whites, deep blacks, subtle grays) with highly intentional, muted accent colors for metadata badges (e.g., a soft, sophisticated amber or muted teal).
* **Surfaces:** Utilize subtle translucency and background blurs (glassmorphism) sparingly to indicate depth, rather than solid borders.

## Animation & Micro-interactions (Framer Motion)
* **Intentionality:** Animations should be subtle, fluid, and purposeful. No bouncy or exaggerated spring physics. Use smooth easing curves.
* **Layout Transitions:** When new tokens stream in or messages are added, the chat window must smoothly scroll and expand using Framer Motion's `layout` prop.
* **Context Badges:** Metadata tags (Intent, Hardware) should elegantly fade and slide into view above the message bubble.
* **Thinking State:** Replace standard loading spinners with a sophisticated, gently pulsing gradient or a minimalist text fade indicating the agent's reasoning phase.

## Specific UI Components
* **Chat Input:** A text area that auto-expands with multi-line queries. It should have a clean, borderless appearance that subtly highlights on focus and gracefully dims when the AI is generating.
* **Zero-Hallucination Fallback:** If the AI triggers a circuit breaker fallback, the message bubble should feature a very subtle visual shift (like a muted amber indicator) to signify a low-confidence rejection.