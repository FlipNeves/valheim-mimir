import os
from typing import Optional

import chromadb
from chromadb.api.client import ClientAPI

from core import config
from core.settings import settings

_client: Optional[ClientAPI] = None

def get_chroma_client() -> ClientAPI:
    global _client
    if _client is None:
        chroma_path = os.path.join(config.DATA_DIR, "chroma_db")
        os.makedirs(chroma_path, exist_ok=True)
        _client = chromadb.PersistentClient(path=chroma_path)
    return _client

def get_or_create_collection(name: str):
    return get_chroma_client().get_or_create_collection(
        name=name,
        metadata={"hnsw:space": settings.chroma_space},
    )

def delete_by_slug(collection_name: str, slug: str) -> None:
    """Remove todos os chunks de uma página antes de reindexá-la (evita órfãos)."""
    if not slug:
        return
    collection = get_or_create_collection(collection_name)
    try:
        collection.delete(where={"slug": slug})
    except Exception:
        pass

def query_collection(
    collection_name: str,
    query_embedding: list[float],
    top_k: int = 5,
) -> dict:
    collection = get_or_create_collection(collection_name)
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
