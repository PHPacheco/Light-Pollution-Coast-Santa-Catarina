import os
from pathlib import Path


ENV_FILE = Path(__file__).resolve().parent / ".env"
PROJECT_ID_ENV = "EARTH_ENGINE_PROJECT_ID"


def carregar_env(caminho=ENV_FILE):
    if not caminho.exists():
        return

    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue

        chave, valor = linha.split("=", 1)
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        if chave and chave not in os.environ:
            os.environ[chave] = valor


def obter_project_id():
    carregar_env()
    project_id = os.environ.get(PROJECT_ID_ENV)
    if not project_id:
        raise RuntimeError(
            f"Configure {PROJECT_ID_ENV} no arquivo .env antes de usar o Earth Engine."
        )
    return project_id
