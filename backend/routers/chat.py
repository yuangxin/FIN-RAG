import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from services.chat_service import ask_question
from config import NODE_NAMES

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    citations: list
    workflow_steps: list
    metadata: dict


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Synchronous chat endpoint."""
    result = ask_question(request.question)
    return ChatResponse(**result)


@router.websocket("/api/chat/ws")
async def chat_ws(websocket: WebSocket):
    """WebSocket chat endpoint with streaming pipeline steps and tokens."""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            question = data.get("question", "")

            if not question:
                await websocket.send_json({"type": "error", "message": "Empty question"})
                continue

            from workflows.rag_pipeline import rag_pipeline

            initial_state = {
                "question": question,
                "retry_count": 0,
                "workflow_steps": [],
            }

            try:
                final_state = None
                async for event in rag_pipeline.astream_events(
                    initial_state, version="v2"
                ):
                    kind = event["event"]
                    name = event.get("name", "")

                    # Node start notification
                    if kind == "on_chain_start" and name in NODE_NAMES:
                        await websocket.send_json({
                            "type": "step",
                            "node": name,
                            "status": "started",
                        })

                    # Node completion notification
                    if kind == "on_chain_end" and name in NODE_NAMES:
                        output = event.get("data", {}).get("output", {})
                        step_data = {}

                        if name == "query_rewriter":
                            step_data["rewritten"] = output.get("rewritten_question", "")
                        elif name == "metadata_extractor":
                            step_data["company_name"] = output.get("company_name", "")
                            step_data["year"] = output.get("year", "")
                        elif name == "retriever":
                            docs = output.get("documents", [])
                            step_data["doc_count"] = len(docs)

                        await websocket.send_json({
                            "type": "step",
                            "node": name,
                            "status": "completed",
                            "data": step_data,
                        })

                    # LLM token streaming
                    if kind == "on_llm_stream":
                        chunk = event.get("data", {}).get("chunk")
                        if chunk and hasattr(chunk, "content") and chunk.content:
                            await websocket.send_json({
                                "type": "token",
                                "content": chunk.content,
                            })

                    # Capture final state
                    if kind == "on_chain_end" and name == "answer_generator":
                        final_state = event.get("data", {}).get("output", {})

                # Pipeline completed - send final result
                await websocket.send_json({
                    "type": "done",
                    "answer": (final_state or {}).get("answer", ""),
                    "citations": (final_state or {}).get("citations", []),
                    "chart_data": (final_state or {}).get("chart_data"),
                    "workflow_steps": (final_state or {}).get("workflow_steps", []),
                })

            except Exception as e:
                import traceback
                traceback.print_exc()
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                })

    except WebSocketDisconnect:
        pass
