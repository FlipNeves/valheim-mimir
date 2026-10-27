"""Validação ponta a ponta numa amostra pequena.

Scrapeia algumas páginas com o extractor corrigido, indexa numa coleção de
teste (bge-m3 + cosine + IDs estáveis) e faz perguntas em português.

Uso:  python -m scripts.validate_sample
"""
import time

from core.console import enable_utf8
from core import text_utils, exporter

enable_utf8()
from providers import wiki
from services.rag_service import RAGService
from repositories import chroma_repo

TEST_COLLECTION = "wiki_rag_test"

SAMPLE_URLS = [
    "https://valheim.fandom.com/wiki/Iron_mace",
    "https://valheim.fandom.com/wiki/Bronze",
    "https://valheim.fandom.com/wiki/Eikthyr",
    "https://valheim.fandom.com/wiki/Troll",
    "https://valheim.fandom.com/wiki/Fine_wood",
]

QUESTIONS = [
    "Quais materiais preciso para criar a maça de ferro?",
    "Como eu consigo bronze?",
    "Como derroto o Eikthyr?",
]

def main():
    rag = RAGService()

    client = chroma_repo.get_chroma_client()
    try:
        client.delete_collection(TEST_COLLECTION)
    except Exception:
        pass

    print("=== Indexando amostra ===")
    for url in SAMPLE_URLS:
        data = wiki.scrape_page(url)
        if not data:
            print(f"  [FALHA] {url}")
            continue
        exporter.export_page(data)
        chunks = text_utils.split_text_into_chunks(
            exporter._build_rag_text(data), title=data["title"]
        )
        rag._index_chunks(chunks, {**data, "content": ""}, TEST_COLLECTION)
        print(f"  [OK] {data['title']} → {len(chunks)} chunk(s)")
        time.sleep(1.5)

    count = chroma_repo.get_or_create_collection(TEST_COLLECTION).count()
    print(f"\nColeção de teste: {count} chunks\n")

    print("=== Perguntas ===")
    for q in QUESTIONS:
        res = rag.ask(q, collection_name=TEST_COLLECTION)
        print(f"\nP: {q}")
        print(f"R: {res['answer']}")
        srcs = ", ".join(f"{s['title']} ({s['similarity']})" for s in res["sources"])
        print(f"   fontes: {srcs or '—'} | chunks usados: {res['chunks_used']}")

if __name__ == "__main__":
    main()
