"""Roteador de geração de texto.

Por padrão (`LLM_PROVIDER=auto`) usa o Ollama local; se o Ollama não estiver
disponível, cai automaticamente para o Gemini. Só a GERAÇÃO passa por aqui —
os embeddings continuam sempre no Ollama.
"""
import requests

from core.settings import settings
from providers import ollama

_ollama_up_cache = None
_gemini_mod = None


def _ollama_up() -> bool:
    global _ollama_up_cache
    if _ollama_up_cache is None:
        try:
            host = settings.ollama_host.rstrip("/")
            r = requests.get(f"{host}/api/tags", timeout=2)
            _ollama_up_cache = r.status_code == 200
        except Exception:
            _ollama_up_cache = False
    return _ollama_up_cache


def _gemini():
    global _gemini_mod
    if _gemini_mod is None:
        from providers import gemini
        _gemini_mod = gemini
    return _gemini_mod


def active_provider() -> str:
    p = settings.llm_provider.lower()
    if p in ("ollama", "gemini"):
        return p
    return "ollama" if _ollama_up() else "gemini"


def _dispatch(fn_name: str, *args, **kwargs):
    p = settings.llm_provider.lower()
    if p == "gemini":
        return getattr(_gemini(), fn_name)(*args, **kwargs)
    if p == "ollama":
        return getattr(ollama, fn_name)(*args, **kwargs)

    if _ollama_up():
        try:
            return getattr(ollama, fn_name)(*args, **kwargs)
        except Exception:
            if settings.gemini_api_key:
                return getattr(_gemini(), fn_name)(*args, **kwargs)
            raise
    return getattr(_gemini(), fn_name)(*args, **kwargs)


def chat_with_context(*args, **kwargs):
    return _dispatch("chat_with_context", *args, **kwargs)


def rewrite_query_en(*args, **kwargs):
    return _dispatch("rewrite_query_en", *args, **kwargs)


def translate_text(*args, **kwargs):
    return _dispatch("translate_text", *args, **kwargs)
