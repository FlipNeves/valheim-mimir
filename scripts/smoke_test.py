"""Smoke test do ambiente: valida imports, Ollama (LLM + embeddings) e ChromaDB.

Uso:  python -m scripts.smoke_test
Sai com código 0 se tudo passar, 1 caso contrário.
"""
import sys
import os

from core.console import enable_utf8

enable_utf8()

OK = "[OK]"
FAIL = "[FALHA]"

LLM_MODEL = os.environ.get("LLM_MODEL", "qwen2.5:7b-instruct")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "bge-m3")
EMBED_QUERY_PREFIX = os.environ.get("EMBED_QUERY_PREFIX", "")

def check(label: str, fn):
    try:
        detail = fn()
        print(f"{OK} {label}" + (f" — {detail}" if detail else ""))
        return True
    except Exception as e:
        print(f"{FAIL} {label} — {type(e).__name__}: {e}")
        return False

def _imports():
    import cloudscraper, bs4, fastapi, uvicorn, ollama, chromadb, pydantic
    return f"chromadb {chromadb.__version__}, pydantic {pydantic.VERSION}"

def _ollama_up():
    import ollama
    models = [m.get("model", "") for m in ollama.list().get("models", [])]
    return f"{len(models)} modelo(s) instalado(s)"

def _embed():
    import ollama
    resp = ollama.embeddings(model=EMBED_MODEL, prompt=f"{EMBED_QUERY_PREFIX}o que é bronze?")
    dim = len(resp["embedding"])
    return f"{EMBED_MODEL} → vetor de {dim} dims"

def _llm():
    import ollama
    resp = ollama.generate(model=LLM_MODEL, prompt="Responda apenas: OK")
    return f"{LLM_MODEL} respondeu ({len(resp['response'].strip())} chars)"

def _chroma():
    import chromadb
    client = chromadb.EphemeralClient()
    col = client.get_or_create_collection("smoke", metadata={"hnsw:space": "cosine"})
    col.add(ids=["a"], embeddings=[[0.1, 0.2, 0.3]], documents=["teste"])
    n = col.count()
    return f"cosine collection OK, {n} doc"

def main():
    print("=== Smoke test do ambiente Valheim RAG ===\n")
    results = [
        check("Imports das dependências", _imports),
        check("Ollama respondendo", _ollama_up),
        check(f"Embeddings ({EMBED_MODEL})", _embed),
        check(f"LLM ({LLM_MODEL})", _llm),
        check("ChromaDB (cosine)", _chroma),
    ]
    print()
    if all(results):
        print("Tudo certo. Ambiente pronto para rodar o pipeline.")
        sys.exit(0)
    else:
        print("Alguns checks falharam. Veja acima. (Ollama rodando? Modelos baixados?)")
        sys.exit(1)

if __name__ == "__main__":
    main()
