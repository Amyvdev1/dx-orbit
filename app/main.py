from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .core import analyze_openapi, compare_reports, markdown_report

BASE = Path(__file__).resolve().parent
app = FastAPI(title="DX Orbit", version="1.0.0", description="Developer Experience Observatory for OpenAPI contracts")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


class ComparePayload(BaseModel):
    before: dict[str, Any]
    after: dict[str, Any]


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(BASE / "static" / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "dx-orbit", "version": "1.0.0"}


@app.post("/api/analyze")
def analyze(spec: dict[str, Any]) -> dict[str, Any]:
    return analyze_openapi(spec)


@app.post("/api/analyze-file")
async def analyze_file(file: UploadFile = File(...)) -> dict[str, Any]:
    raw = await file.read()
    if len(raw) > 2_000_000:
        raise HTTPException(status_code=413, detail="OpenAPI document exceeds 2 MB demo limit")
    try:
        if file.filename and file.filename.lower().endswith((".yaml", ".yml")):
            spec = yaml.safe_load(raw)
        else:
            spec = json.loads(raw)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid OpenAPI document: {exc}") from exc
    if not isinstance(spec, dict):
        raise HTTPException(status_code=400, detail="OpenAPI root must be an object")
    return analyze_openapi(spec)


@app.post("/api/compare")
def compare(payload: ComparePayload) -> dict[str, Any]:
    return compare_reports(payload.before, payload.after)


@app.post("/api/report/markdown", response_class=PlainTextResponse)
def report_markdown(spec: dict[str, Any]) -> str:
    return markdown_report(analyze_openapi(spec))
