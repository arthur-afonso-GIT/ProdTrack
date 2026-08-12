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

import os
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path


def _base_dir() -> Path:
    """
    Resolve a pasta base do aplicativo.
    Em uma instalação Windows, os dados ficam no perfil gravável do usuário,
    separados dos binários instalados. Em desenvolvimento, usamos o projeto.
    """
    if getattr(sys, "frozen", False):
        local_app_data = os.environ.get("LOCALAPPDATA")
        path = Path(local_app_data) / "ProdTrack" if local_app_data else Path.home() / ".prodtrack"
        path.mkdir(parents=True, exist_ok=True)
        return path
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
                hora_inicio TEXT,
                hora_fim TEXT,
                evidencia TEXT,                      -- link ou caminho de arquivo
                observacoes TEXT,
                criado_em TEXT DEFAULT (datetime('now', 'localtime')),
                atualizado_em TEXT DEFAULT (datetime('now', 'localtime'))
            );
            """
        )

        # Migra bancos existentes sem apagar dados.
        colunas_atividades = {
            row["name"] for row in conn.execute("PRAGMA table_info(atividades);").fetchall()
        }
        if "hora_inicio" not in colunas_atividades:
            conn.execute("ALTER TABLE atividades ADD COLUMN hora_inicio TEXT;")
        if "hora_fim" not in colunas_atividades:
            conn.execute("ALTER TABLE atividades ADD COLUMN hora_fim TEXT;")

        # Tabela de configurações (jornada diária, diretórios, etc.)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            );
            """
        )

        # Modelos reutilizáveis criados pelo usuário para registros frequentes.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS atividades_fixas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_atividade TEXT NOT NULL,
                tempo_minutos INTEGER NOT NULL CHECK (tempo_minutos > 0),
                evidencia TEXT DEFAULT '',
                observacoes TEXT DEFAULT '',
                criado_em TEXT DEFAULT (datetime('now', 'localtime'))
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
