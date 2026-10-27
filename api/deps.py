"""Dependências compartilhadas da API — hoje, autenticação opcional por chave.

Enquanto API_KEY estiver vazio (padrão local), nada é exigido. Ao publicar,
basta definir API_KEY no .env que todos os endpoints do router passam a exigir
o header `X-API-Key`.
"""
import time
import threading
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request, status

from core.settings import settings

def require_api_key(x_api_key: str | None = Header(default=None)):
    if not settings.api_key:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API inválida ou ausente (header X-API-Key).",
        )

_rl_lock = threading.Lock()
_rl_hits: dict[str, deque] = defaultdict(deque)

def rate_limit(request: Request, x_api_key: str | None = Header(default=None)):
    limit = settings.rate_limit_per_minute
    if limit <= 0:
        return
    key = x_api_key or (request.client.host if request.client else "anon")
    now = time.time()
    with _rl_lock:
        hits = _rl_hits[key]
        while hits and now - hits[0] > 60:
            hits.popleft()
        if len(hits) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas requisições. Aguarde um instante e tente de novo.",
            )
        hits.append(now)
