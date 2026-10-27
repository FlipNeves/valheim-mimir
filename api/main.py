import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.endpoints import router
from core import config
from core.console import enable_utf8
from core.settings import settings
from providers import llm

enable_utf8()
config.ensure_dirs()

app = FastAPI(
    title="Mímir — Valheim Wiki RAG API",
    description="O guardião do conhecimento nórdico responde sobre Valheim.",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["infra"])
def health():
    provider = llm.active_provider()
    active_model = settings.gemini_model if provider == "gemini" else settings.llm_model
    return {
        "status": "ok",
        "provider": provider,
        "llm": active_model,
        "embed": settings.embed_model,
    }


if __name__ == "__main__":
    uvicorn.run("api.main:app", host=settings.api_host, port=settings.api_port, reload=True)
