"""
services/backup_service.py
Backup automático (e manual) do banco de dados SQLite.
Mantém um histórico limitado de backups na pasta configurada pelo
usuário (Configurações → diretório de backups), removendo os mais
antigos quando o limite é excedido.
"""

import shutil
from datetime import datetime
from pathlib import Path

import models
from database import DB_PATH

MAX_BACKUPS = 30  # quantidade máxima de arquivos de backup a manter


def _dir_backups_atual() -> Path:
    """Lê o diretório de backups configurado, garantindo que ele exista."""
    caminho = Path(models.obter_dir_backups())
    caminho.mkdir(parents=True, exist_ok=True)
    return caminho


def criar_backup() -> Path:
    """
    Copia o arquivo atual do banco para a pasta de backups configurada,
    nomeando com data/hora. Retorna o caminho do backup criado.
    """
    if not DB_PATH.exists():
        raise FileNotFoundError("Banco de dados ainda não foi criado.")

    dir_backups = _dir_backups_atual()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = dir_backups / f"prodtrack_backup_{timestamp}.db"
    shutil.copy2(DB_PATH, destino)

    _limpar_backups_antigos(dir_backups)
    return destino


def _limpar_backups_antigos(dir_backups: Path) -> None:
    """Mantém apenas os MAX_BACKUPS backups mais recentes na pasta informada."""
    backups = sorted(dir_backups.glob("prodtrack_backup_*.db"), key=lambda p: p.stat().st_mtime)
    excedentes = len(backups) - MAX_BACKUPS
    for arquivo in backups[: max(excedentes, 0)]:
        arquivo.unlink(missing_ok=True)


def listar_backups() -> list[dict]:
    """Retorna lista de backups existentes (na pasta configurada), mais recente primeiro."""
    dir_backups = _dir_backups_atual()
    backups = sorted(
        dir_backups.glob("prodtrack_backup_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return [
        {
            "nome": b.name,
            "caminho": str(b),
            "tamanho_kb": round(b.stat().st_size / 1024, 1),
            "criado_em": datetime.fromtimestamp(b.stat().st_mtime).strftime("%d/%m/%Y %H:%M:%S"),
        }
        for b in backups
    ]


def deve_fazer_backup_diario() -> bool:
    """
    Verifica se já existe algum backup criado hoje na pasta configurada.
    Usado para disparar backup automático uma vez por dia/sessão.
    """
    try:
        dir_backups = _dir_backups_atual()
    except Exception:  # noqa: BLE001
        return False
    hoje = datetime.now().strftime("%Y%m%d")
    backups_hoje = list(dir_backups.glob(f"prodtrack_backup_{hoje}_*.db"))
    return len(backups_hoje) == 0


def restaurar_backup(caminho_backup: str) -> None:
    """
    Restaura o banco a partir de um arquivo de backup.
    ATENÇÃO: sobrescreve o banco atual (um backup de segurança do
    estado atual é feito automaticamente antes de restaurar).
    """
    origem = Path(caminho_backup)
    if not origem.exists():
        raise FileNotFoundError(f"Arquivo de backup não encontrado: {caminho_backup}")

    if DB_PATH.exists():
        criar_backup()

    shutil.copy2(origem, DB_PATH)
