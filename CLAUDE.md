# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

10-K Financial QA System — a Financial Document Q&A system. Users upload SEC filings (10-K/10-Q PDFs), then ask questions answered via a LangGraph RAG pipeline. Full-stack: FastAPI backend + React frontend.

## Commands

```bash
# Backend
cd backend && pip install -r requirements.txt          # install deps
uvicorn main:app --reload --port 8000                  # run server

# Frontend
cd frontend && npm install                             # install deps
npm run dev                                            # run dev server (port 5173)

# Tests
cd backend && pytest tests/ -v                         # run all tests
pytest tests/test_workflow.py -v                       # run single test file
pytest tests/test_embeddings.py::test_embedding_dimension -v  # run single test

# If pip fails with SSL on Chinese mirrors, use:
pip install -r requirements.txt -i https://pypi.org/simple/ --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

## Architecture

### RAG Pipeline (LangGraph 4-node graph)

```
START → query_rewriter → metadata_extractor → retriever ──→ route_after_retrieval
                                                              │
                                                    docs found? → answer_generator → END
                                                    no docs + retries left? → query_rewriter (retry)
```

- `workflows/rag_pipeline.py` — assembles the StateGraph, compiles it
- `core/state.py` — `RAGState` TypedDict shared across all nodes
- `edges/route_after_retrieval.py` — conditional routing based on retrieval results

### Backend Layer Separation

| Layer | Directory | Role |
|-------|-----------|------|
| Core | `core/` | LLM, embeddings, vector store, document parser, state, prompts |
| Nodes | `nodes/` | LangGraph node functions (each takes state, returns state update) |
| Edges | `edges/` | Conditional routing functions |
| Workflows | `workflows/` | Graph assembly |
| Services | `services/` | Business logic called by routers |
| Routers | `routers/` | FastAPI endpoints + WebSocket |

### Frontend Structure

- `hooks/useChat.js` — WebSocket connection, streaming tokens, pipeline step tracking. Uses `pendingQuestion` ref to queue messages before WebSocket opens.
- `hooks/useDocuments.js` — Document CRUD state
- `pages/DashboardPage.jsx` — Main layout: sidebar (w-80, documents) + chat panel + financial charts
- `index.css` — Glassmorphism CSS classes (`glass`, `glass-sidebar`, `glass-header`, `glass-input`, `chat-bubble-user`, `chat-bubble-bot`, `doc-card`, `btn-gradient`, etc.). Dark mode is default.
- All components accept `darkMode` prop for dual glass/light styling

### Key Design Decisions

- **No document grader**: Uses Top-10 retrieval instead of LLM-per-doc grading to save API calls
- **No hallucination checker**: Relies on prompt engineering ("answer based ONLY on provided documents")
- **Supplemental financial retrieval**: When query mentions financial metrics, retriever also pulls from `item_8_financials` section directly via `FINANCIAL_KEYWORDS` list in `nodes/retriever.py`
- **10-K section-aware chunking**: `document_parser.py` uses regex patterns from `config.py` (`SECTION_PATTERNS`) to split by SEC Item sections. Tables preserved as whole chunks.
- **Per-page error isolation**: `document_parser.py` wraps each page in try-catch. On failure, degrades to text-only (no table extraction). Pages are never skipped entirely.
- **Async file uploads**: `routers/documents.py` uses `asyncio.to_thread()` for `process_upload()` to avoid blocking the event loop on large PDFs.
- **Vector store batching**: `vector_store.py` inserts documents in batches of `VECTOR_STORE_BATCH_SIZE` (100) to avoid memory spikes with large documents.
- **Singleton instances**: `llm`, `embedding_model`, `vector_store`, `terminology_dict` are module-level singletons
- **Document registry is in-memory**: `_document_registry` in `services/document_service.py` — auto-restored from ChromaDB on startup, but lost if ChromaDB is cleared
- **Terminology-enhanced retrieval**: Financial terms expanded at both query time (dictionary + LLM) and chunk time (enriched embeddings). See `core/terminology.py` and `data/terminology.json`
- **Inline chart generation**: Comparison-type questions (multi-year, multi-metric) auto-generate Recharts charts inside chat messages. Single-year questions do not. See `nodes/answer_generator.py` chart extraction and `ChatMessage.jsx` rendering

### Configuration

All settings in `backend/config.py`: LLM model, embedding model, chunk sizes, section patterns, company aliases, retry limits, vector store batch size.

Environment: `.env` at project root needs `DEEPSEEK_API_KEY`.

### WebSocket Protocol (`/api/chat/ws`)

Client sends: `{"type": "question", "question": "..."}`

Server streams:
1. `{"type": "step", "node": "query_rewriter", "status": "started"}` per node
2. `{"type": "step", "node": "...", "status": "completed", "data": {...}}` on completion
3. `{"type": "token", "content": "..."}` during LLM generation
4. `{"type": "done", "answer": "...", "citations": [...], "chart_data": {...}|null, "workflow_steps": [...]}` at end

### Vite Proxy

`frontend/vite.config.js` proxies `/api/*` to `http://localhost:8000` with `timeout: 600000` (10 min). WebSocket hook (`useChat.js`) connects directly to `ws://localhost:8000/api/chat/ws` (not through proxy). CORS in `backend/main.py` allows ports 5173, 5174, 3000.
