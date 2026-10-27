import hashlib
from typing import Optional

from ollama import Client

from core.settings import settings
from core.prompts import MIMIR_SYSTEM_PROMPT, REWRITE_PROMPT, build_user_message

_client = Client(host=settings.ollama_host)

SYSTEM_PROMPT = MIMIR_SYSTEM_PROMPT

def generate_deterministic_id(content: str, title: str) -> str:
    raw_data = f"{title}|{content}"
    return hashlib.sha256(raw_data.encode("utf-8")).hexdigest()

def rewrite_query_en(question: str, model: Optional[str] = None) -> str:
    """Reescreve a pergunta (PT) como uma query curta de busca em inglês.

    Melhora muito o match de nomes próprios de itens no embedding multilíngue.
    Retorna a query em inglês, ou a pergunta original se algo falhar.
    """
    model = model or settings.llm_model
    try:
        resp = _client.generate(
            model=model,
            prompt=REWRITE_PROMPT.format(q=question),
            keep_alive=settings.ollama_keep_alive,
            options=_llm_options({"temperature": 0.0}),
        )
        out = resp["response"].strip().strip('"').splitlines()[0].strip()
        return out or question
    except Exception:
        return question

def translate_text(text: str, target_lang: str = "en", model: Optional[str] = None) -> str:
    """Traduz *text* usando o LLM local. Opcional — não é usado no caminho padrão
    de pergunta (o embedding multilíngue dispensa tradução)."""
    model = model or settings.llm_model
    lang_label = "English" if target_lang == "en" else "Brazilian Portuguese"
    prompt = (
        f"Translate to {lang_label}. Output ONLY the translated text, no explanations.\n"
        f"Text: {text}\n"
        "Translation:"
    )
    try:
        response = _client.generate(
            model=model, prompt=prompt,
            keep_alive=settings.ollama_keep_alive, options=_llm_options(),
        )
        return response["response"].strip()
    except Exception:
        return text

def _prefix(is_query: bool) -> str:
    return settings.embed_query_prefix if is_query else settings.embed_doc_prefix

def _embed_options() -> Optional[dict]:
    if settings.embed_num_gpu >= 0:
        return {"num_gpu": settings.embed_num_gpu}
    return None

def _llm_options(extra: Optional[dict] = None) -> Optional[dict]:
    opts = dict(extra) if extra else {}
    if settings.llm_num_gpu >= 0:
        opts["num_gpu"] = settings.llm_num_gpu
    return opts or None

def generate_embedding(text: str, is_query: bool = False) -> list[float]:
    """Gera o embedding de um texto. `is_query=True` aplica o prefixo de consulta."""
    resp = _client.embeddings(
        model=settings.embed_model,
        prompt=f"{_prefix(is_query)}{text}",
        options=_embed_options(),
        keep_alive=settings.ollama_keep_alive,
    )
    return resp["embedding"]

def embed_batch(texts: list[str], is_query: bool = False) -> list[list[float]]:
    """Gera embeddings em lote — bem mais rápido que 1 a 1 na indexação."""
    if not texts:
        return []
    prefix = _prefix(is_query)
    inputs = [f"{prefix}{t}" for t in texts]
    resp = _client.embed(
        model=settings.embed_model,
        input=inputs,
        options=_embed_options(),
        keep_alive=settings.ollama_keep_alive,
    )
    return resp["embeddings"]

def chat_with_context(
    question: str,
    context_chunks: list,
    history: Optional[list[dict]] = None,
    model: Optional[str] = None,
    system_prompt: str = SYSTEM_PROMPT,
) -> str:
    model = model or settings.llm_model
    user_message = build_user_message(question, context_chunks)

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    response = _client.chat(
        model=model, messages=messages,
        keep_alive=settings.ollama_keep_alive,
        options=_llm_options({"temperature": settings.llm_temperature}),
    )
    return response["message"]["content"]
