# Super Brain (WhatsApp Assistant) - Specifications

This document outlines the current features, architecture, and configuration of **Super Brain**, our WhatsApp AI Assistant deployed to interface natively with the Meta Cloud API.

## Core Features
1. **Interactive Text Messaging**
   - Receives and processes WhatsApp text queries seamlessly in near real-time.
   - Conversational, contextual, and intelligent AI responses powered directly by Google Gemini v1.5 Pro.

2. **Retrieval-Augmented Generation (RAG) Memory**
   - Trigger term: `"remember this: <fact>"` embeds notes individually per-user context.
   - Saves parsed text chunks as vectors embedded using `models/embedding-001` via Supabase Vector.
   - Any query runs a similarity seek within Supabase before injecting relevant memory fragments right back into the System prompt for an integrated answer context.

3. **Multi-Modal Graceful Degradation**
   - Automatically detects and drops complex attachment types (like images, video, audio, files).
   - Serves clear fallback dummy strings prompting humans to engage effectively in text interfaces only until logic blocks are scaled out. 

4. **Meta Console Authentication Engine**
   - Includes full Webhook Subscription lifecycle routes. 
   - Uses `hub.challenge` tokens to respond to Facebook Dev portal verifications.
   - Computes robust HMAC SHA256 Webhook payload validations preventing any malicious man-in-the-middle attacks to your server endpoint utilizing the secure Meta Access Token. 

## Tech Stack Overview
- **Routing**: `FastAPI` + `uvicorn` mapping HTTP routes completely asynchronously. Native web static payloads (`index`, `privacy`) serving directly.
- **Agent Intelligence**: `langchain` + `Google Gemini` API endpoints.
- **Vector Database**: **Supabase Vector (pgvector)**. 
- **Persisted Store**: **Supabase (PostgreSQL)** saving unstructured chat log events + document bindings.
- **Client Networking**: Meta Cloud API (`httpx` asynchronous graph dispatcher bounds).

## Scalability Hooks Built
- Currently utilizing `BackgroundTasks` heavily to isolate external Meta/Gemini inference timeouts, immediately returning the API `200 ACCEPTED` status. This correctly complies strictly with WhatsApp strict 30-sec roundtrip thresholds. 
- Supabase-backed architecture allows for horizontal scaling and serverless deployment.

*Generated: April 2026*
