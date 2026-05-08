# 🧠 Super Brain: The Ultimate Personal AI Assistant on WhatsApp

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![LLM](https://img.shields.io/badge/AI-Gemini%201.5%20Pro-orange.svg)](https://deepmind.google/technologies/gemini/)
[![VectorDB](https://img.shields.io/badge/VectorDB-Supabase%20Vector-green.svg)](https://supabase.com/docs/guides/ai)

**Super Brain** is an enterprise-grade personal AI assistant that lives natively inside WhatsApp. Unlike standard chatbots, it features persistent long-term memory via Retrieval-Augmented Generation (RAG), proactive reminder scheduling, and multimodal capabilities, all served through a secure, high-performance asynchronous architecture.

---

## 🚀 Key Features

### 🏛️ Long-Term Memory (RAG)
*   **Semantic Retrieval**: Uses Google's `embedding-001` model to vectorize and store personal facts in **Supabase Vector (pgvector)**.
*   **Persistent Recall**: Automatically retrieves relevant memories during conversation to provide personalized, context-aware responses.
*   **Self-Cleaning Memory**: Intelligently updates or deletes conflicting memories (e.g., "I moved to London" replaces your previous "I live in Paris" note).

### ⏰ Intelligent Reminders & Scheduling
*   **Natural Language Entry**: "Remind me to call Mom in 2 hours."
*   **Interactive Controls**: Includes WhatsApp interactive buttons for **Snooze (10m/1h)** and **Mark as Done**.
*   **Async Scheduler**: Powered by `APScheduler` for precision delivery of time-sensitive alerts.

### 🎙️ Multimodal Intelligence
*   **Vision & Voice**: Processes images (receipts, prescriptions), voice notes, and audio files.
*   **Auto-Knowledge Extraction**: Summarizes media content and automatically saves it to long-term memory for later text-based search.

### 🎭 Adaptive Personality
*   **Onboarding Flow**: Dynamic WhatsApp-native onboarding to capture user name and preferred tone (Formal, Casual, or Sarcastic).
*   **Contextual Awareness**: Maintains short-term conversation buffers to follow complex, multi-turn dialogues.

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Backend Framework** | FastAPI (Asynchronous Python) |
| **LLM Engine** | Google Gemini 1.5 Pro |
| **Vector Database** | Supabase Vector (pgvector) |
| **Primary Database** | Supabase (PostgreSQL) |
| **Messaging API** | Meta Cloud API (WhatsApp Business) |
| **Task Scheduling** | APScheduler |
| **Networking** | HTTPX (Async HTTP Dispatcher) |
| **Validation** | HMAC SHA-256 Webhook Verification |

---

## 🏗️ Architecture & Security

### High-Performance Pipeline
To comply with Meta's strict **30-second roundtrip threshold**, Super Brain utilizes a non-blocking asynchronous pipeline:
1.  **Ingress**: FastAPI receives the webhook and immediately validates the **HMAC SHA-256 signature**.
2.  **Parallel Fetching**: History, RAG context, and reminders are fetched concurrently using `asyncio.gather`.
3.  **Background Processing**: The LLM inference and database writes (logging, memory updates) are pushed to **BackgroundTasks**, allowing the API to return a `200 OK` safely while the user receives their reply.

### Project Structure
```text
├── app/
│   ├── conversation/   # Orchestration & Assistant Logic
│   ├── database/       # Abstract DB layer (Supabase)
│   ├── llm/            # Gemini API Integration
│   ├── rag/            # Vector indexing & Semantic search
│   ├── scheduler/      # Reminder engine & Task queuing
│   └── whatsapp/       # Meta Webhook handlers & Signature validation
├── public/             # Admin Dashboard & Static Assets
├── main.py             # FastAPI Entry Point
└── requirements.txt    # Dependency Manifest
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
*   Python 3.10+
*   Google AI Studio API Key (Gemini)
*   Meta Developer Account (WhatsApp Cloud API)
*   Supabase Project (Required for Vector storage and persistence)

### 2. Quick Start
```bash
# Clone and install
git clone https://github.com/your-repo/whats-app-automation.git
cd whats-app-automation
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API Keys
```

### 3. Run Locally
```bash
uvicorn main:app --reload --port 8000
```

---

## 📈 Dashboard & Monitoring
Super Brain includes a built-in administrative suite:
*   **/admin**: Real-time stats dashboard.
*   **/api/admin/conversations**: Monitor assistant interactions.
*   **/privacy-policy**: Pre-built compliance page for Meta App review.

---

## 👨‍💻 Note for Recruiters
This project demonstrates several advanced software engineering principles:
*   **Asynchronous Programming**: Extensive use of `async/await` and concurrent task execution.
*   **RAG & Vector Embeddings**: Practical implementation of AI memory management.
*   **Production Security**: Implementation of payload signature verification.
*   **Scalability**: Modular architecture with clear separation of concerns.

---

## 🗺️ Roadmap
- [ ] Using redis queue for background tasks and scheduling.
- [ ] PDF document parsing and knowledge extraction.
- [ ] Integration with Google Calendar.
- [ ] Deployment to Docker/Kubernetes.

---
*Created with ❤️ by Razamindset*