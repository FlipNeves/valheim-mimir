# Mímir — Valheim Wiki → RAG → Mod

Um **oráculo de Valheim**: extrai a [Valheim Wiki](https://valheim.fandom.com/wiki/Valheim_Wiki),
indexa em um banco vetorial e responde perguntas em português como **Mímir**, o
guardião do conhecimento nórdico — 100% local (Ollama), exposto via **API** e
consumido por um **mod BepInEx** dentro do jogo.

```
/mimir como eu consigo bronze?
Mímir: Você precisará fundir cobre e estanho no Forge para obter bronze.
```

## Arquitetura

```
Wiki → scraping → chunks → embeddings (bge-m3) → ChromaDB (cosine)
                                                        │
              pergunta PT ──► embedding ──► busca ──► contexto
                                                        │
                                          qwen2.5 (persona Mímir) ──► resposta
                                                        ▲
                                        API FastAPI ◄── Mod Valheim (/mimir)
```

Decisões de projeto que importam para performance/qualidade:
- **bge-m3** (embedding multilíngue): casa perguntas em PT com o corpus em inglês
  **sem tradução** → metade da latência por pergunta.
- **ChromaDB em cosine** + filtro de similaridade real (chunks irrelevantes são descartados).
- **IDs estáveis** (`slug::índice`): reindexar não gera duplicatas órfãs.
- **Embed na CPU + LLM na GPU** (`EMBED_NUM_GPU=0`): em GPUs de ~6GB os dois modelos
  ficam residentes ao mesmo tempo, sem swap. Levou a latência de ~48s → ~3s/pergunta.

## Pré-requisitos

- **Python 3.12** (o ChromaDB não tem wheels estáveis no 3.14)
- **Ollama** com os modelos:
  ```bash
  ollama pull qwen2.5:7b-instruct   # geração (voz do Mímir)
  ollama pull bge-m3                 # embeddings multilíngues
  ```

## Setup (Windows)

Instalação one-shot via winget + venv:

```bash
winget install Python.Python.3.12
winget install Ollama.Ollama
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

O `setup.ps1` cria o `.venv`, instala dependências, gera `requirements.lock.txt`,
copia `.env.example → .env` e baixa os modelos. Validação do ambiente:

```bash
python -m scripts.smoke_test
```

## Configuração

Tudo vem de `.env` (veja `.env.example`). Principais chaves:

| Chave | Padrão | Descrição |
|---|---|---|
| `LLM_MODEL` | `qwen2.5:7b-instruct` | Modelo de geração |
| `EMBED_MODEL` | `bge-m3` | Modelo de embeddings |
| `EMBED_NUM_GPU` | `0` | Embed na CPU (evita swap em GPU pequena). `-1` = GPU |
| `CHROMA_SPACE` | `cosine` | Métrica de distância |
| `RAG_MIN_SIMILARITY` | `0.3` | Similaridade mínima para um chunk entrar no contexto |
| `SCRAPE_MIN/MAX_DELAY` | `1.0` / `2.0` | Delay entre requisições à wiki |
| `API_KEY` | *(vazio)* | Se preenchido, a API exige header `X-API-Key` |

## Pipeline de dados

```bash
python pipeline.py                       # completo: descoberta → scraping → embed
python pipeline.py --scrape-only         # re-scrapeia usando o page_manifest.json
python pipeline.py --embed-only --reset-collection   # reindexa do zero no Chroma
```

Para reindexar rápido (LLM ocioso), use a GPU no embed:

```bash
EMBED_NUM_GPU=-1 python pipeline.py --embed-only --reset-collection
```

## Usar

Chatbot no terminal:
```bash
python chat.py
```

API REST:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```
- `GET  /health` — status + modelos
- `POST /rag/ask` — pergunta ao Mímir (aceita `top_k`, `min_similarity`, `history`)
- `GET  /rag/documents` — lista chunks indexados
- `POST /scrape/extract` — extrai e indexa uma URL
- Docs interativas: `http://localhost:8000/docs`

## Mod de Valheim

O mod BepInEx que traz o Mímir para o chat do jogo está em [`mod/`](mod/README.md).

## Estrutura

```
├── pipeline.py         # Pipeline CLI (scraping → embedding)
├── chat.py             # Chatbot no terminal
├── api/                # FastAPI (endpoints + auth + health)
├── services/           # Orquestração do RAG
├── repositories/       # ChromaDB
├── providers/          # Scraper, discovery, Ollama
├── core/               # settings, prompts (persona), config, exporter, utils
├── domain/             # Schemas Pydantic
├── scripts/            # setup, smoke_test, validate_sample
├── mod/                # Mod BepInEx (C#)
└── data/               # json / rag_chunks / chroma_db
```
