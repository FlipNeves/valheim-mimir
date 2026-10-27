"""Sobe o Cloudflare Tunnel para a API local e publica a URL da sessão num
repositório do GitHub (commit + push), para o mod resolver o endereço atual.

Uso:  python -m scripts.serve_public   (com a API já rodando em start_api.bat)
Requer no .env: ENDPOINT_REPO_DIR (clone local do repo do endpoint).
"""
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

from core.console import enable_utf8

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

enable_utf8()

PORT = os.getenv("API_PORT", "8000")
REPO_DIR = os.getenv("ENDPOINT_REPO_DIR", "")
ENDPOINT_FILE = os.getenv("ENDPOINT_FILE", "endpoint.txt")
CLOUDFLARED = os.getenv("CLOUDFLARED_PATH") or shutil.which("cloudflared")

URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def _fail(msg: str):
    print(msg)
    sys.exit(1)


def _publish(url: str):
    path = os.path.join(REPO_DIR, ENDPOINT_FILE)
    stamp = datetime.now(timezone.utc).isoformat()
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{url}\natualizado: {stamp}\n")
    subprocess.run(["git", "-C", REPO_DIR, "add", ENDPOINT_FILE], check=True)
    subprocess.run(["git", "-C", REPO_DIR, "commit", "-m", "Atualizando endpoint do Mimir"], check=True)
    subprocess.run(["git", "-C", REPO_DIR, "push"], check=True)
    print(f"\n>>> URL publicada no GitHub: {url}\n")


def main():
    if not CLOUDFLARED:
        _fail("cloudflared não encontrado. Rode 'winget install Cloudflare.cloudflared' "
              "ou defina CLOUDFLARED_PATH no .env.")
    if not REPO_DIR or not os.path.isdir(os.path.join(REPO_DIR, ".git")):
        _fail("Defina ENDPOINT_REPO_DIR no .env apontando para o CLONE local do repo do endpoint.")

    print(f"Subindo Cloudflare Tunnel para http://localhost:{PORT} ...")
    proc = subprocess.Popen(
        [CLOUDFLARED, "tunnel", "--url", f"http://localhost:{PORT}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, encoding="utf-8", errors="replace",
    )

    published = False
    try:
        for line in proc.stdout:
            print(line, end="")
            if not published:
                match = URL_RE.search(line)
                if match:
                    published = True
                    try:
                        _publish(match.group(0))
                    except subprocess.CalledProcessError as e:
                        print(f"Falha ao publicar no git: {e}")
                    print("=== Túnel no ar. Deixe esta janela aberta enquanto jogam. ===\n")
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        print("\nTúnel encerrado.")


if __name__ == "__main__":
    main()
