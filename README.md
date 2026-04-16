# WhatsApp Personal AI Assistant

A Python-based AI assistant for WhatsApp that uses Google Gemini for intelligence and LangChain/Chroma for long-term memory (RAG).

## Features
- **WhatsApp Integration**: Receive and send messages via Twilio.
- **AI Intelligence**: Powered by Google Gemini API.
- **RAG Memory**: Remembers specific information with "remember this: [text]" command.
- **Context Awareness**: Remembers the last 5-10 messages in a conversation.
- **Async Architecture**: Built with FastAPI and SQLAlchemy (aiosqlite) for high performance.
- **Modular Design**: Easy to swap SQLite for PostgreSQL or MySQL.

## Project Structure
```text
whatsapp_assistant/
├── main.py                 # FastAPI app entry point
├── app/
│   ├── database/           # Abstract DB layer & SQLite implementation
│   ├── rag/                # RAG indexing and retrieval logic
│   ├── llm/                # Gemini API wrapper
│   ├── whatsapp/           # Twilio webhook & sender logic
│   └── conversation/       # Orchestration logic
└── tests/                  # Unit tests
```

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- A Google Gemini API Key
- A Twilio Account (for WhatsApp Sandbox)
- [ngrok](https://ngrok.com/) for exposing the local server

### 2. Installation
1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\\Scripts\\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Configuration
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Fill in your API keys in `.env`.

### 4. Initialization
Initialize the database:
```bash
python -m app.database.sqlite_impl --init
```

### 5. Running the Application
Start the FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```

### 6. Webhook Setup
1. Expose your local port 8000 using ngrok:
   ```bash
   ngrok http 8000
   ```
2. Copy the forwarding URL (e.g., `https://xxxx.ngrok.io`).
3. In your Twilio Console -> Messaging -> Try it Out -> WhatsApp Sandbox:
   - Set "When a message comes in" to: `https://xxxx.ngrok.io/webhook/whatsapp`

## Commands
- **Store Memory**: Send "remember this: [anything you want to remember]"
- **Regular Chat**: Just send any message, and the AI will reply using its memory if relevant.

## Phase 2 (Future)
- Voice message transcription.
- Image/PDF processing.
- Multi-user data isolation improvements.
- Migration to PostgreSQL.
