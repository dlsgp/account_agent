from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.expenses import router as expenses_router
from app.api.receivables import router as receivables_router
from app.api.summaries import router as summaries_router
from app.web import router as web_router

app = FastAPI(title="AI Account Agent")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(web_router)
app.include_router(expenses_router)
app.include_router(summaries_router)
app.include_router(receivables_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
