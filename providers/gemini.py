import time
from typing import Optional

from core.settings import settings
from core.prompts import MIMIR_SYSTEM_PROMPT, REWRITE_PROMPT, build_user_message

SYSTEM_PROMPT = MIMIR_SYSTEM_PROMPT

_client = None


def _get_client():
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY não definido. Configure no .env para usar o Gemini."
            )
        from google import genai
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _generate(contents, system_instruction: Optional[str] = None,
              temperature: Optional[float] = None, retries: int = 2) -> str:
    from google.genai import types, errors
    cfg_kwargs = {}
    if system_instruction:
        cfg_kwargs["system_instruction"] = system_instruction
    if temperature is not None:
        cfg_kwargs["temperature"] = temperature
    config = types.GenerateContentConfig(**cfg_kwargs) if cfg_kwargs else None

    last_err = None
    for attempt in range(retries + 1):
        try:
            resp = _get_client().models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=config,
            )
            return (resp.text or "").strip()
        except errors.ServerError as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise last_err


def rewrite_query_en(question: str, model: Optional[str] = None) -> str:
    try:
        out = _generate(REWRITE_PROMPT.format(q=question), temperature=0.0)
        first = out.splitlines()[0].strip().strip('"') if out else ""
        return first or question
    except Exception:
        return question


def translate_text(text: str, target_lang: str = "en", model: Optional[str] = None) -> str:
    lang_label = "English" if target_lang == "en" else "Brazilian Portuguese"
    prompt = (
        f"Translate to {lang_label}. Output ONLY the translated text, no explanations.\n"
        f"Text: {text}\n"
        "Translation:"
    )
    try:
        return _generate(prompt, temperature=0.0) or text
    except Exception:
        return text


def chat_with_context(
    question: str,
    context_chunks: list,
    history: Optional[list[dict]] = None,
    model: Optional[str] = None,
    system_prompt: str = SYSTEM_PROMPT,
) -> str:
    user_message = build_user_message(question, context_chunks)

    contents = []
    for msg in history or []:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    return _generate(contents, system_instruction=system_prompt,
                     temperature=settings.llm_temperature)
