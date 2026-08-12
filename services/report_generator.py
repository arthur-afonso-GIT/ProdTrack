"""
services/report_generator.py
Geração de relatórios em PDF (diário, mensal, trimestral, semestral
ou período livre) usando ReportLab. Os relatórios incluem cabeçalho,
resumo do período e uma tabela detalhada das atividades.

Esta camada também sabe salvar o PDF gerado no diretório de relatórios
configurado pelo usuário (ver models.obter_dir_relatorios), já que a
aplicação desktop não tem "download" — o arquivo precisa ir direto
para uma pasta no disco.
"""

from datetime import date, datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

import models


def _estilos():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TituloRelatorio",
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=4,
            textColor=colors.HexColor("#1F2937"),
            fontName="Helvetica-Bold",
        )
    )
    styles.add(
        ParagraphStyle(
            name="Subtitulo",
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#6B7280"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SecaoTitulo",
            fontSize=12,
            leading=16,
            spaceBefore=10,
            spaceAfter=6,
            textColor=colors.HexColor("#1F2937"),
            fontName="Helvetica-Bold",
        )
    )
    styles.add(
        ParagraphStyle(
            name="TextoNormalPequeno",
            fontSize=9,
            leading=12,
            alignment=TA_LEFT,
        )
    )
    return styles


def _cabecalho_elementos(titulo: str, subtitulo: str, styles):
    return [
        Paragraph(titulo, styles["TituloRelatorio"]),
        Paragraph(subtitulo, styles["Subtitulo"]),
        Spacer(1, 0.5 * cm),
    ]


def _tabela_resumo(resumo: dict, jornada_horas: int):
    dados = [
        ["Indicador", "Valor"],
        ["Quantidade de atividades", str(resumo["qtd_atividades"])],
        ["Total de horas trabalhadas", resumo["total_horas_str"]],
        ["Total em minutos", str(resumo["total_minutos"])],
        ["Jornada de referência", f"{jornada_horas}h/dia"],
        ["Percentual da meta atingido", f"{resumo.get('percentual_meta', 0)}%"],
    ]
    tabela = Table(dados, colWidths=[8 * cm, 8 * cm])
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return tabela


def _tabela_detalhada(df: pd.DataFrame):
    cabecalho = ["Data", "Atividade", "Tempo", "Horário", "Evidência", "Observações"]
    linhas = [cabecalho]
    body_style = getSampleStyleSheet()["BodyText"]

    for _, row in df.sort_values("data").iterrows():
        data_str = row["data"].strftime("%d/%m/%Y") if hasattr(row["data"], "strftime") else str(row["data"])
        linhas.append(
            [
                data_str,
                Paragraph(str(row["nome_atividade"]), body_style),
                models.minutos_para_horas_str(row["tempo_minutos"]),
                (
                    f'{row.get("hora_inicio")}–{row.get("hora_fim")}'
                    if row.get("hora_inicio") and row.get("hora_fim") else "-"
                ),
                Paragraph(str(row.get("evidencia") or "-"), body_style),
                Paragraph(str(row.get("observacoes") or "-"), body_style),
            ]
        )

    tabela = Table(
        linhas,
        colWidths=[2.0 * cm, 3.7 * cm, 1.5 * cm, 1.8 * cm, 3.6 * cm, 3.6 * cm],
        repeatRows=1,
    )
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tabela


def gerar_relatorio_pdf_bytes(
    df: pd.DataFrame,
    titulo: str,
    data_inicio: date,
    data_fim: date,
    jornada_horas: int,
    dias_meta: int = 1,
) -> bytes:
    """Gera o relatório e retorna os bytes do PDF (sem salvar em disco)."""
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )
    styles = _estilos()

    subtitulo = (
        f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
        f" — Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

    elementos = _cabecalho_elementos(titulo, subtitulo, styles)

    resumo = models.resumo_periodo(df)
    resumo["percentual_meta"] = models.percentual_meta(resumo["total_minutos"], jornada_horas, dias=dias_meta)

    elementos.append(Paragraph("Resumo do Período", styles["SecaoTitulo"]))
    elementos.append(_tabela_resumo(resumo, jornada_horas))
    elementos.append(Spacer(1, 0.8 * cm))

    elementos.append(Paragraph("Detalhamento das Atividades", styles["SecaoTitulo"]))
    if df.empty:
        elementos.append(Paragraph("Nenhuma atividade registrada neste período.", styles["TextoNormalPequeno"]))
    else:
        elementos.append(_tabela_detalhada(df))

    doc.build(elementos)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def gerar_relatorio_pdf(
    df: pd.DataFrame,
    titulo: str,
    data_inicio: date,
    data_fim: date,
    jornada_horas: int,
    dias_meta: int = 1,
    nome_arquivo: str | None = None,
) -> Path:
    """
    Gera o relatório em PDF e salva no diretório de relatórios configurado
    pelo usuário (Configurações). Retorna o Path do arquivo salvo.
    """
    pdf_bytes = gerar_relatorio_pdf_bytes(df, titulo, data_inicio, data_fim, jornada_horas, dias_meta)

    dir_relatorios = Path(models.obter_dir_relatorios())
    dir_relatorios.mkdir(parents=True, exist_ok=True)

    if not nome_arquivo:
        nome_arquivo = f"relatorio_{data_inicio.strftime('%Y%m%d')}_{data_fim.strftime('%Y%m%d')}.pdf"

    destino = dir_relatorios / nome_arquivo
    destino.write_bytes(pdf_bytes)
    return destino
