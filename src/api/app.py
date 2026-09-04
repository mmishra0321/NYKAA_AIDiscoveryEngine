"""Nykaa Fashion wishlist discovery API — Groq keys never leave the server."""

from __future__ import annotations

import os
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from src.api.ask import answer_ask
from src.api.store import (
    catalog_markdown,
    flatten_themes,
    get_catalog,
    pipeline_summary,
    scrape_status,
)

app = FastAPI(title="Nykaa Fashion Wishlist Discovery", version="1.0.0")

_origins = [
    o.strip()
    for o in (os.getenv("FRONTEND_ORIGINS") or "http://127.0.0.1:5173,http://localhost:5173").split(",")
    if o.strip()
]
_cors_kw: dict[str, Any] = {
    "allow_origins": _origins,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if (os.getenv("ALLOW_VERCEL_ORIGINS") or "1").strip() in {"1", "true", "yes"}:
    _cors_kw["allow_origin_regex"] = r"https://.*\.vercel\.app"
app.add_middleware(CORSMiddleware, **_cors_kw)


class AskBody(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class ExportBody(BaseModel):
    format: str = "markdown"


@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    catalog_ok = True
    try:
        report = get_catalog()
        n = len(report.questions)
    except FileNotFoundError:
        catalog_ok = False
        n = 0
    return {"status": "ok" if catalog_ok else "degraded", "catalog": catalog_ok, "questions": n}


@app.get("/api/v1/pipeline/summary")
def pipeline() -> dict[str, Any]:
    return pipeline_summary()


@app.get("/api/v1/scrape/status")
def scrape() -> dict[str, Any]:
    """Last scrape log + latest GitHub Actions ingest run."""
    return scrape_status()


@app.get("/api/v1/catalog")
def catalog() -> dict[str, Any]:
    try:
        return get_catalog().model_dump(mode="json")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/v1/themes")
def themes() -> dict[str, Any]:
    try:
        report = get_catalog()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"themes": flatten_themes(report)}


@app.get("/api/v1/insights/{query_id}")
def insights(query_id: str) -> dict[str, Any]:
    try:
        report = get_catalog()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    for q in report.questions:
        if q.id == query_id:
            return q.model_dump(mode="json")
    raise HTTPException(status_code=404, detail=f"Unknown question {query_id}")


@app.post("/api/v1/ask")
def ask(body: AskBody) -> dict[str, Any]:
    try:
        report = get_catalog()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return answer_ask(body.question, report)


@app.post("/api/v1/export")
def export_catalog(body: Optional[ExportBody] = None) -> Response:
    fmt = ((body.format if body else None) or "markdown").lower().strip()
    try:
        report = get_catalog()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if fmt in {"md", "markdown"}:
        text = catalog_markdown() or ""
        return PlainTextResponse(
            text,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="nykaa-wishlist-catalog.md"'},
        )
    if fmt == "json":
        payload = report.model_dump_json()
        return Response(
            content=payload,
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="nykaa-wishlist-catalog.json"'},
        )
    raise HTTPException(status_code=400, detail="format must be markdown or json")


@app.get("/")
def root() -> JSONResponse:
    return JSONResponse({"service": "nykaa-fashion-wishlist", "docs": "/docs"})
