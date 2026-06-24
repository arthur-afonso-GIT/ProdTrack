"""
services/excel_service.py
Exportação e importação de atividades em formato Excel (.xlsx).
Usado pela tela de Configurações (export/import completo) e pela
tela de Relatórios (export do período filtrado).
"""

from pathlib import Path

import pandas as pd

import models


def exportar_atividades_para_excel(df, destino: Path) -> Path:
    """
    Exporta um DataFrame de atividades (no formato bruto do banco) para
    um arquivo .xlsx no caminho indicado. Retorna o Path do arquivo salvo.
    """
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    df_formatado = models.exportar_para_dataframe(df)
    with pd.ExcelWriter(destino, engine="openpyxl") as writer:
        df_formatado.to_excel(writer, index=False, sheet_name="Atividades")

    return destino


def importar_atividades_de_excel(caminho_arquivo: Path) -> tuple[int, list[str]]:
    """
    Lê um arquivo .xlsx do caminho informado e importa as atividades
    contidas nele. Retorna (quantidade_importada, lista_de_erros).
    """
    df_importado = pd.read_excel(caminho_arquivo)
    return models.importar_de_dataframe(df_importado)
