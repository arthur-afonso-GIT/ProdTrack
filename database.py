"""
database.py
Camada de acesso ao banco de dados SQLite do ProdTrack (aplicação desktop).

Responsável por:
- localizar a pasta base da aplicação (funciona tanto em modo script
  quanto quando empacotado como executável, ex.: PyInstaller);
- criar as tabelas na primeira execução;
- fornecer conexões via context manager.

Esta camada não depende de nenhum framework de UI — pode ser usada
isoladamente em testes ou em scripts utilitários.
"""

import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path


def _base_dir() -> Path:
    """
    Resolve a pasta base do aplicativo.
    Quando empacotado com PyInstaller, sys.executable apontará para o
    binário gerado; em modo desenvolvimento, usamos a pasta deste arquivo.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR = _base_dir()
DB_PATH = BASE_DIR / "database.db"

# Diretórios padrão (usados na primeira execução; podem ser
# sobrescritos pelo usuário na tela de Configurações — ver models.py)
DEFAULT_BACKUPS_DIR = BASE_DIR / "backups"
DEFAULT_RELATORIOS_DIR = BASE_DIR / "relatorios"
ASSETS_DIR = BASE_DIR / "assets"

for _dir in (DEFAULT_BACKUPS_DIR, DEFAULT_RELATORIOS_DIR, ASSETS_DIR):
    _dir.mkdir(exist_ok=True)


@contextmanager
def get_connection():
    """
    Context manager que entrega uma conexão SQLite já configurada
    (row_factory para acesso tipo dict) e garante commit/rollback e
    fechamento corretos da conexão.
    """
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """
    Cria as tabelas do banco caso ainda não existam (idempotente).
    Deve ser chamada uma vez na inicialização do aplicativo.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # Tabela principal de atividades de teletrabalho
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS atividades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,                 -- formato YYYY-MM-DD
                nome_atividade TEXT NOT NULL,
                tempo_minutos INTEGER NOT NULL CHECK (tempo_minutos > 0),
                evidencia TEXT,                      -- link ou caminho de arquivo
                observacoes TEXT,
                criado_em TEXT DEFAULT (datetime('now', 'localtime')),
                atualizado_em TEXT DEFAULT (datetime('now', 'localtime'))
            );
            """
        )

        # Tabela de configurações (jornada diária, diretórios, etc.)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            );
            """
        )

        # Índices para acelerar busca/filtro por data e nome da atividade
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_atividades_data ON atividades(data);"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_atividades_nome ON atividades(nome_atividade);"
        )

        # Valores padrão de configuração, inseridos apenas se ainda não existirem
        defaults = {
            "jornada_diaria_horas": "8",
            "dir_relatorios": str(DEFAULT_RELATORIOS_DIR),
            "dir_backups": str(DEFAULT_BACKUPS_DIR),
        }
        for chave, valor in defaults.items():
            cur.execute(
                "INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES (?, ?);",
                (chave, valor),
            )
