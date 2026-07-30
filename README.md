# AraCheck 🏥 — Arabic AI Medical Assistant & RAG Pipeline

![AraCheck Banner](https://img.shields.io/badge/AraCheck-Medical%20AI%20Assistant-blue?style=for-the-badge&logo=fastapi)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-red?style=for-the-badge)](https://qdrant.tech/)
[![Whisper](https://img.shields.io/badge/Whisper-STT-green?style=for-the-badge)](https://github.com/openai/whisper)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**AraCheck** is an end-to-end, medical AI agent platform tailored specifically for Arabic healthcare queries. The system combines Retrieval-Augmented Generation (RAG) over medical literature, Speech-to-Text (Whisper STT), Vision-Language Models (VLM) for medical image understanding, and medical PDF ingestion into a high-performance vector search database (Qdrant).

---

## 🛠️ Tech Stack

### Backend
* **FastAPI**: Asynchronous web framework for high-throughput REST APIs.
* **LangGraph & LangChain**: Agentic workflow orchestration with history-aware context management.
* **Groq Cloud / HuggingFace**: High-speed LLM inference backend (utilizing `llama-3.3-70b-versatile`).
* **Qdrant**: High-density Vector Database for chunk embedding retrieval.
* **Faster-Whisper**: Speech-to-Text engine optimized for Arabic dialect and medical terminology.
* **Pydantic & SlowAPI**: Strict request/response validation and rate limiting.

### Frontend
* **Next.js 15 (App Router)**: Modern React framework with Server-Side Rendering (SSR).
* **React 19 & TypeScript**: Type-safe interactive user interface components.
* **Tailwind CSS & Shadcn UI**: Sleek, responsive medical chat interface with dark mode support.

### Infrastructure & DevOps
* **Docker & Docker Compose**: Containerized multi-service deployment.
* **PowerShell Automation (`start_all.ps1`)**: Single-command launcher for local development environment.

---

## 📡 API Endpoints

### 1. `POST /chat`
* **Description**: Interact with the core Medical AI Agent pipeline (integrating RAG, history trimming, and safety guardrails).
* **Request Body** (`application/json`):
  ```json
  {
    "message": "What are the early symptoms of hypertension?",
    "history": [
      {"role": "user", "content": "Hello"},
      {"role": "assistant", "content": "Hello! How can I assist with your medical questions today?"}
    ]
  }
  ```
* **Response** (`200 OK`):
  ```json
  {
    "response": "Hypertension often has no initial symptoms, but may present with headaches or shortness of breath...",
    "sources": ["Medical_Guide_PDF_Page_12"]
  }
  ```

### 2. `POST /transcribe`
* **Description**: Convert voice notes into text using Faster-Whisper (supports Arabic & English).
* **Request Body** (`multipart/form-data`):
  * `file`: Audio file (`wav`, `mp3`, `m4a`, `webm`, `ogg` - max 25 MB).
  * `language` (optional): `"ar"` or `"en"`.
* **Response** (`200 OK`):
  ```json
  {
    "text": "I have been experiencing a sore throat and fever for two days.",
    "language": "ar"
  }
  ```

### 3. `POST /analyze-image`
* **Description**: Analyze medical images, prescriptions, or lab reports using Vision-Language Models (VLM).
* **Request Body** (`multipart/form-data`):
  * `file`: Image file (`jpeg`, `png`, `webp` - max 10 MB).
* **Response** (`200 OK`):
  ```json
  {
    "extracted_text": "Paracetamol 500mg - Take 1 tablet every 8 hours",
    "visual_description": "Prescription document with handwritten dosage instructions.",
    "error": null
  }
  ```

### 4. `POST /upload-pdf`
* **Description**: Ingest and index medical PDF books into Qdrant vector database for RAG retrieval.
* **Request Body** (`multipart/form-data`):
  * `file`: Medical document (`pdf` - max 25 MB).
* **Response** (`200 OK`):
  ```json
  {
    "filename": "cardiology_handbook.pdf",
    "total_pages": 14,
    "total_chunks": 42,
    "status": "success"
  }
  ```

### 5. `GET /flags`
* **Description**: List all active runtime feature flags and their current status.
* **Response** (`200 OK`):
  ```json
  {
    "ENABLE_VOICE_INPUT": true,
    "ENABLE_PDF_INGESTION": true,
    "ENABLE_IMAGE_ANALYSIS": true
  }
  ```

### 6. `PATCH /flags/{flag_name}`
* **Description**: Dynamically toggle a feature flag at runtime without restarting the server.
* **Headers**: `x-admin-key: <ADMIN_SECRET_KEY>`
* **Request Body** (`application/json`):
  ```json
  {
    "enabled": false
  }
  ```
* **Response** (`200 OK`):
  ```json
  {
    "flag": "ENABLE_VOICE_INPUT",
    "enabled": false,
    "status": "updated"
  }
  ```

### 7. `GET /health`
* **Description**: Backend health check endpoint verifying service operational readiness.
* **Response** (`200 OK`):
  ```json
  {
    "status": "ok",
    "service": "AraCheck Backend",
    "version": "1.0.0"
  }
  ```

---

## 📂 Project Structure

```
AraCheck/
├── configs/                # Hyperparameters & config for QLoRA fine-tuning (Qwen2.5)
├── frontend/               # Next.js 15 frontend application
│   ├── app/                # App Router pages and routes
│   ├── components/         # Interactive UI components (Chat, File Uploaders)
│   └── public/             # Static assets
├── scripts/                # Utility scripts for data ingestion
├── src/                    # Primary Backend Application Package
│   ├── agent_pipeline/     # LangGraph agent nodes & prompt definitions
│   ├── core/               # History context manager & payload validation
│   ├── rag_ingestion/      # PDF text extraction & Qdrant vector indexing
│   ├── rag_retrieval/      # Hybrid retriever & cross-encoder reranker
│   ├── schemas/            # Pydantic request/response model contracts
│   ├── stt_pipeline/       # Whisper speech-to-text pipeline
│   ├── main.py             # FastAPI Application Entry Point
│   └── settings.py         # App configuration & runtime feature flags
├── tests/                  # Automated integration & endpoint test suite
├── start_all.ps1           # One-click PowerShell dev launcher
├── Dockerfile              # Backend production container configuration
├── docker-compose.yml      # Full-stack Docker Compose setup
└── requirements.txt        # Backend Python dependencies
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root with the following configuration:

```env
# ─── LLM & Cloud Provider Keys ───
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
HF_TOKEN=hf_your_huggingface_token_here

# ─── Qdrant Vector Database ───
QDRANT_URL=https://your-qdrant-cluster-url.qdrant.tech
QDRANT_API_KEY=your_qdrant_api_key

# ─── Speech-to-Text (Whisper) ───
WHISPER_MODEL=small

# ─── Security & Origin Controls ───
ADMIN_SECRET_KEY=your-custom-admin-secret-key
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# ─── Feature Flags ───
ENABLE_VOICE_INPUT=true
ENABLE_PDF_INGESTION=true
ENABLE_IMAGE_ANALYSIS=true
```

For the Frontend (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚩 Dynamic Feature Flags

AraCheck includes a runtime feature flag system allowing administrators to disable or enable sub-services without server restarts:

1. **Initial State via `.env`**: Set `ENABLE_VOICE_INPUT=false` to disable at boot time.
2. **Runtime Mutation**:
   Toggle live using the Admin API:
   ```bash
   curl -X PATCH "http://localhost:8000/flags/ENABLE_VOICE_INPUT" \
        -H "x-admin-key: your-custom-admin-secret-key" \
        -H "Content-Type: application/json" \
        -d '{"enabled": false}'
   ```

---

## 🚀 Installation & Setup

### Option 1: Fast One-Click Launcher (Windows PowerShell)
Launches backend and frontend in separate parallel windows:
```powershell
.\start_all.ps1
```

### Option 2: Docker Compose
```bash
docker-compose up --build
```
* **Backend API**: `http://localhost:8000` (Docs: `http://localhost:8000/docs`)
* **Frontend UI**: `http://localhost:3000`

### Option 3: Manual Setup

1. **Backend**:
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate # Windows: .venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Start FastAPI server
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 🧪 Running Tests

Execute automated endpoint smoke tests:
```bash
python tests/test_endpoints.py
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.

1. Fork the Repository
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

