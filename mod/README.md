# Mímir — Mod de Valheim (Oráculo da Wiki)

Um mod BepInEx que traz **Mímir**, o guardião do conhecimento nórdico, para dentro
do Valheim. O jogador digita no chat e Mímir responde consultando a API RAG local.

```
/mimir como eu consigo bronze?
Mímir: Você precisará fundir cobre e estanho no Forge para obter bronze.
```

## Pré-requisitos

1. **Valheim** com **BepInEx** instalado (via [Thunderstore/r2modman](https://valheim.thunderstore.io/package/denikson/BepInExPack_Valheim/) ou manual).
2. A **API do Mímir rodando** (o servidor FastAPI deste repositório):
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8000
   ```
3. **.NET SDK** (6+) para compilar. [Baixar](https://dotnet.microsoft.com/download).

## Compilar

Na raiz do mod:

```bash
dotnet build -c Release
```

Se o Valheim **não** estiver no caminho padrão do Steam, aponte a instalação:

```bash
dotnet build -c Release -p:ValheimDir="D:\Games\Valheim"
```

O build referencia os DLLs do jogo em `valheim_Data\Managed` e do BepInEx em
`BepInEx\core`. A saída é `MimirMod.dll`.

## Instalar

Copie `bin\Release\MimirMod.dll` para:

```
<Valheim>\BepInEx\plugins\MimirMod.dll
```

Inicie o jogo. No primeiro boot é criado o arquivo de config
`BepInEx\config\com.flipneves.mimir.cfg`.

## Configurar

Edite `com.flipneves.mimir.cfg` (ou via gerenciador de config do BepInEx):

| Chave | Padrão | Descrição |
|---|---|---|
| `[API] Url` | `http://localhost:8000` | Base da API do Mímir |
| `[API] ApiKey` | *(vazio)* | Header `X-API-Key`, se a API exigir |
| `[Chat] Command` | `/mimir` | Prefixo que invoca o Mímir |

## Como funciona

- `ChatPatch.cs` — patch Harmony em `Terminal.InputText()`. Captura o texto cru
  digitado no chat; se começar com o prefixo, trata como pergunta e bloqueia o
  envio normal (não vai para outros jogadores).
- `MimirPlugin.cs` — dispara `UnityWebRequest` (POST `/rag/ask`) numa coroutine
  (thread-safe no Unity) e imprime a resposta no chat como "Mímir".

## Notas

- A resposta é **local** (só quem perguntou vê), então funciona em multiplayer
  sem enviar nada aos outros.
- Consultas levam alguns segundos (o LLM local gera a resposta). Mímir mostra
  "*medita sobre a tua pergunta...*" enquanto processa.
- Para uso público/remoto, aponte `[API] Url` para o servidor onde a API está
  hospedada e configure `ApiKey`.
