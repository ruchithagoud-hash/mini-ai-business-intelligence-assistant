"""main.py - FastAPI backend.

Run:  uvicorn main:app --reload
Docs: http://127.0.0.1:8000/docs
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from analytics import answer_question, data_quality
from db import DEFAULT_DB_PATH, DatabaseNotReady

logger = logging.getLogger("bi_api")

app = FastAPI(
    title="Mini AI Business Intelligence Assistant",
    description="Ask natural-language questions about the sales dataset.",
    version="1.0.0",
)


def get_db_path() -> Path:
    """Database location (override with the BI_DB_PATH environment variable)."""
    return Path(os.getenv("BI_DB_PATH", str(DEFAULT_DB_PATH)))


class AskRequest(BaseModel):
    question: str = Field(..., max_length=500, examples=["What are the total sales?"])

    @field_validator("question")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question must not be empty.")
        return value


class AskResponse(BaseModel):
    question: str
    supported: bool
    intent: str | None = None
    method: str
    answer: str
    columns: list[str]
    rows: list[dict[str, Any]]
    sql: str | None = None
    formula: str


class HealthResponse(BaseModel):
    status: str
    database_ready: bool
    llm_configured: bool


@app.get("/health", response_model=HealthResponse)
def health(db_path: Path = Depends(get_db_path)) -> HealthResponse:
    try:
        ready = data_quality(db_path)["total_records"] > 0
    except Exception:
        ready = False
    return HealthResponse(
        status="ok", database_ready=ready, llm_configured=bool(os.getenv("OPENAI_API_KEY"))
    )


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, db_path: Path = Depends(get_db_path)) -> AskResponse:
    try:
        return AskResponse(**answer_question(request.question, db_path))
    except DatabaseNotReady as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        logger.exception("Unexpected error while answering a question")
        raise HTTPException(
            status_code=500, detail="Internal error while answering the question."
        )
