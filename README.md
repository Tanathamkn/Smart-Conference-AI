# 🎙️ Smart Conference AI

An AI-powered meeting intelligence system that transcribes, summarizes, and extracts insights from meeting audio files — with support for mixed **Thai-English** speech.

## ✨ Features

- 🎧 **Audio Upload** — Upload `.mp3`, `.wav`, or `.m4a` meeting recordings
- 📝 **Speech-to-Text** — Thai-English transcription powered by `faster-whisper` (`large-v3`)
- 🤖 **AI Summarization** — Automatic meeting summaries, key topics, and decisions via Typhoon LLM
- ✅ **Action Item Extraction** — Detects tasks, owners, and due dates from conversations
- ⚠️ **Issue & Risk Detection** — Identifies problems and proposed solutions
- 🔍 **Semantic Search** — Natural-language search across all meetings using `bge-m3` embeddings + pgvector
- 💬 **Meeting Q&A** — Ask questions and get AI-generated answers grounded in meeting content
- 👥 **30+ Concurrent Users** — Designed to handle at least 30 simultaneous search/query users

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   React Frontend │────▶│   FastAPI Backend     │────▶│  PostgreSQL +   │
│   (Vite + TS)   │     │                      │     │  pgvector       │
│   Port: 5173    │     │  - faster-whisper    │     │  Port: 5432     │
└─────────────────┘     │  - bge-m3 embeddings │     └─────────────────┘
                        │  - Typhoon LLM API   │
                        │  Port: 8000          │
                        └──────────────────────┘
```

| Component | Technology |
|---|---|
| Frontend | React 18, Vite, TypeScript, TailwindCSS |
| Backend | FastAPI, SQLAlchemy, Python 3.11 |
| Speech-to-Text | `faster-whisper` (`large-v3`, CPU) |
| Embeddings | `BAAI/bge-m3` via `sentence-transformers` |
| LLM | [Typhoon v2.5](https://opentyphoon.ai) (`typhoon-v2.5-30b-a3b-instruct`) |
| Database | PostgreSQL 15 + `pgvector` extension |
| Containerization | Docker + Docker Compose |

---

## 🚀 Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac/Linux)
- A [Typhoon API Key](https://opentyphoon.ai) from SCB 10X

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd "Smart Conference"
```

### 2. Configure environment variables

Copy the example env file and fill in your API key:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Typhoon LLM API Key (get one at https://opentyphoon.ai)
TYPHOON_API_KEY=your-api-key-here

# Database connection (leave as-is for local Docker)
DATABASE_URL=DATABASE_URL

# Frontend hot-reload (required for Docker on Windows)
CHOKIDAR_USEPOLLING=true
```

### 3. Build and run

```bash
docker-compose up --build
```

> ⚠️ **First run note:** The backend will automatically download the `large-v3` Whisper model (~1.5 GB) and the `bge-m3` embedding model (~2.2 GB) on first startup. This may take 10–20 minutes depending on your internet speed. Subsequent starts are instant.

### 4. Open the app

| Service | URL |
|---|---|
| Frontend UI | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## 📁 Project Structure

```
Smart Conference/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/
│   │   │   └── meetings.py       # All API routes (upload, list, delete, search)
│   │   ├── db/
│   │   │   ├── session.py        # Database session management
│   │   │   └── init_db.py        # Auto-creates tables on startup
│   │   ├── models/
│   │   │   └── db.py             # SQLAlchemy models (Meeting, ActionItem, Issue...)
│   │   ├── services/
│   │   │   ├── audio_processing.py  # faster-whisper transcription (Thai+English)
│   │   │   ├── embedding.py         # bge-m3 vector embeddings
│   │   │   └── llm_processing.py    # Typhoon LLM summarization & Q&A
│   │   └── main.py
│   ├── Dockerfile
│   ├── .dockerignore
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx        # Meeting list
│   │   │   ├── UploadPage.tsx       # Audio upload
│   │   │   ├── MeetingDetails.tsx   # Summary, transcript, action items
│   │   │   └── SearchPage.tsx       # Semantic search & Q&A
│   │   └── App.tsx
│   ├── Dockerfile
│   └── .dockerignore
├── tests/
│   ├── locustfile.py             # Load test (30 concurrent users)
│   └── k6_script.js             # k6 load test script
├── docker-compose.yml
├── .env                          # ← Your secrets (not committed to git)
├── .env.example
└── .gitignore
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/meetings/upload` | Upload an audio file for processing |
| `GET` | `/api/meetings` | List all meetings |
| `GET` | `/api/meetings/{id}` | Get meeting details (transcript, summary, etc.) |
| `DELETE` | `/api/meetings/{id}` | Delete a meeting and all its data |
| `GET` | `/api/search?query=...` | Semantic search + AI Q&A across meetings |

Full interactive documentation available at **http://localhost:8000/docs**

---

## 🧪 Load Testing

The system is designed to support **30+ concurrent search users**.

### Using Locust

```bash
pip install locust
locust -f tests/locustfile.py --host=http://localhost:8000
# Open http://localhost:8089 and set users=30, spawn rate=5
```

### Using k6

```bash
k6 run tests/k6_script.js
```

---

## ⚙️ Configuration

| Variable | Default | Description |
|---|---|---|
| `TYPHOON_API_KEY` | — | **Required.** Your Typhoon API key |
| `DATABASE_URL` | `DATABASE_URL` | PostgreSQL connection string |
| `WHISPER_MODEL_SIZE` | `large-v3` | Whisper model size (`base`, `medium`, `large-v3`) |
| `TYPHOON_BASE_URL` | `https://api.opentyphoon.ai/v1` | Typhoon API base URL |
| `CHOKIDAR_USEPOLLING` | `true` | Required for hot-reload on Windows/Docker |

> **Tip:** Use `WHISPER_MODEL_SIZE=medium` in `.env` for faster processing at the cost of some Thai accuracy.

---

## 🛠️ Development Tips

### View live backend logs

```bash
docker-compose logs -f backend
```

### Restart only the backend (after code changes)

```bash
docker-compose restart backend
```

### Reclaim Docker disk space

```bash
docker system prune -a --volumes -f
```

### Access the database directly

```bash
docker-compose exec db psql -U postgres -d smartconf
```

---

## 📝 Notes

- **Processing time:** An 8-minute audio file takes approximately **10–15 minutes** to process on CPU with `large-v3`. Use `WHISPER_MODEL_SIZE=medium` if speed is more important than accuracy.
- **Language:** The transcription model is pinned to Thai (`language="th"`) which naturally handles mixed Thai-English speech. This prevents misdetection as other languages (e.g., Russian).
- **Storage:** The first `docker-compose up --build` will use approximately **6–8 GB** of disk space for Docker images and ML models.
- **Audio files** are automatically deleted from the server after transcription completes. Only the text transcript is stored in the database.
