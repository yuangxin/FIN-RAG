# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

10-K Financial QA System — SEC financial document Q&A powered by a LangGraph RAG pipeline. Users upload 10-K/10-Q PDF filings, ask questions in natural language, and get cited answers with cross-company comparison and auto chart generation. Backend only (FastAPI + LangGraph + ChromaDB).

## Commands

```bash
# Install & Run
cd backend && pip install -r requirements.txt          # install deps
uvicorn main:app --reload --port 8000                  # run server

# Tests
cd backend && pytest tests/ -v                         # run all tests
pytest tests/test_workflow.py -v                       # run single test file
pytest tests/test_embeddings.py::test_embedding_dimension -v  # run single test

# RAGAS Evaluation
cd backend && jupyter notebook eval_ragas.ipynb        # run RAGAS evaluation notebook

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
| Core | `core/` | LLM, embeddings, vector store, document parser, state, prompts, terminology |
| Nodes | `nodes/` | LangGraph node functions (each takes state, returns state update) |
| Edges | `edges/` | Conditional routing functions |
| Workflows | `workflows/` | Graph assembly |
| Services | `services/` | Business logic called by routers |
| Routers | `routers/` | FastAPI endpoints + WebSocket |

### Key Design Decisions

- **No document grader**: Uses Top-10 retrieval instead of LLM-per-doc grading to save API calls
- **No hallucination checker**: Relies on prompt engineering ("answer based ONLY on provided documents")
- **Hybrid retrieval (Vector + BM25)**: Over-recalls `TOP_K × HYBRID_CANDIDATE_MULTIPLIER` candidates via vector search, then reranks using weighted fusion of normalized vector similarity and BM25Okapi scores (controlled by `HYBRID_ALPHA` in `config.py`). See `nodes/retriever.py` → `_hybrid_rerank()`.
- **Metadata-filtered retrieval**: `metadata_extractor` node uses LLM to extract company name(s), year, quarter from the question, which are then used as ChromaDB `where` filters in all three retrieval passes (main, financial supplemental, risk supplemental). On retry, filters are progressively relaxed (quarter first, then year).
- **Supplemental financial retrieval**: When query mentions financial metrics, retriever also pulls from `item_8_financials` section directly via `FINANCIAL_KEYWORDS` list in `nodes/retriever.py`
- **Supplemental risk retrieval**: When query mentions risk-related keywords, retriever pulls from `item_1a_risk` + `item_7_mda` sections via `RISK_KEYWORDS`
- **Terminology-enhanced retrieval (dual-side)**: 550+ financial terms in `data/terminology.json`. At query time: `terminology_dict.expand_query()` appends synonyms/components to the query before LLM rewriting. At chunk time: `terminology_dict.enrich_chunk_text()` appends term info to chunk text before embedding, improving semantic matching for abbreviations (EPS → "Earnings Per Share, net income, weighted average shares").
- **10-K section-aware chunking**: `document_parser.py` uses regex patterns from `config.py` (`SECTION_PATTERNS`) to split by SEC Item sections. Tables preserved as whole chunks.
- **Per-page error isolation**: `document_parser.py` wraps each page in try-catch. On failure, degrades to text-only (no table extraction). Pages are never skipped entirely.
- **Async file uploads**: `routers/documents.py` uses `asyncio.to_thread()` for `process_upload()` to avoid blocking the event loop on large PDFs.
- **Vector store batching**: `vector_store.py` inserts documents in batches of `VECTOR_STORE_BATCH_SIZE` (100) to avoid memory spikes with large documents.
- **Singleton instances**: `llm`, `embedding_model`, `vector_store`, `terminology_dict` are module-level singletons
- **Document registry is in-memory**: `_document_registry` in `services/document_service.py` — auto-restored from ChromaDB on startup, but lost if ChromaDB is cleared
- **Inline chart generation**: Comparison-type questions (multi-year, multi-metric) auto-generate chart data inside chat responses. See `nodes/answer_generator.py` chart extraction logic.

### Configuration

All settings in `backend/config.py`: LLM model, embedding model, chunk sizes, section patterns, company aliases, retry limits, vector store batch size, hybrid search alpha, terminology expansion toggle.

Environment: `.env` at project root needs `DEEPSEEK_API_KEY`.

### WebSocket Protocol (`/api/chat/ws`)

Client sends: `{"type": "question", "question": "..."}`

Server streams:
1. `{"type": "step", "node": "query_rewriter", "status": "started"}` per node
2. `{"type": "step", "node": "...", "status": "completed", "data": {...}}` on completion
3. `{"type": "token", "content": "..."}` during LLM generation
4. `{"type": "done", "answer": "...", "citations": [...], "chart_data": {...}|null, "workflow_steps": [...]}` at end

### RAGAS Evaluation

RAGAS (ragas v0.4+) is used for systematic RAG pipeline evaluation via `backend/eval_ragas.ipynb` (Jupyter notebook). Key metrics:

- **Faithfulness** — answer grounded in retrieved documents only (validates no-hallucination-checker design)
- **Context Precision** — retrieved docs are relevant (validates Top-10 without grading)
- **Context Recall** — all relevant docs retrieved (validates terminology-enhanced retrieval)
- **Answer Relevancy** — answer addresses the question (validates query rewriter)

Evaluation uses DeepSeek as evaluator LLM via `llm_factory` with `AsyncOpenAI` client, and HuggingFace embeddings for `AnswerRelevancy`. Golden QA dataset: `backend/data/eval_golden_qa.json` (Apple-focused test cases across categories: simple_factual, financial_metrics, yoy_comparison, terminology, table_data, risk_analysis). Results saved to `backend/data/eval_results.json`.

### Sample 10-K PDFs

- `10-k/apple-2025.pdf`, `10-k/nvidia-2024.pdf` — test filings
- `data/terminology.json` — 550+ financial terms dictionary
