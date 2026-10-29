import json
import logging
from typing import Optional, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from langgraph_orchestrator import app as langgraph_app
from database_utils import extract_database_schema


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="FinAssist AI Server")


# Request model
class ChatRequest(BaseModel):
    question: str


# Response model
class ChatResponse(BaseModel):
    summary: str
    data_payload: Optional[list[Any]] = None
    generated_sql: Optional[str] = None


# Chat endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):

    try:
        # Validate the question
        question = request.question.strip()

        if not question:
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty."
            )

        logger.info("Processing question: %s", question)

        # Extract database schema
        schema = extract_database_schema()

        # Initialize LangGraph state
        initial_state = {
            "question": question,
            "schema": schema,
            "sql": None,
            "result": None,
            "error": None,
            "attempts": 0,
            "answer": None
        }

        # Execute the LangGraph workflow
        result_state = langgraph_app.invoke(initial_state)

        # Extract final answer and SQL
        summary = result_state.get(
            "answer"
        )

        generated_sql = result_state.get("sql")

        # Parse database results
        data_payload = None
        db_result = result_state.get("result")

        if db_result:
            try:
                parsed_result = json.loads(db_result)

                if isinstance(parsed_result, list):
                    data_payload = parsed_result

            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    "Database result is not valid JSON."
                )

        # Return response to frontend
        return ChatResponse(
            summary=str(summary),
            data_payload=data_payload,
            generated_sql=generated_sql
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception("Error processing /api/chat")

        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing your request."
        ) from e


# Run using:
# uvicorn api:app --reload --port 8000