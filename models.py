"""
models.py
Regras de negócio e operações de CRUD sobre as atividades de teletrabalho.
Toda a lógica que manipula dados passa por aqui — a camada de UI (ui/)
não deve executar SQL diretamente.
"""

from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd

from database import get_connection, DEFAULT_BACKUPS_DIR, DEFAULT_RELATORIOS_DIR

# --------------------------------------------------------------------------
# CRUD de atividades
# --------------------------------------------------------------------------


def criar_atividade(
    data_atividade: date,
    nome_atividade: str,
    tempo_minutos: int,
    evidencia: str = "",
    observacoes: str = "",
) -> int:
    """Insere uma nova atividade e retorna o ID gerado."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO atividades (data, nome_atividade, tempo_minutos, evidencia, observacoes)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                data_atividade.isoformat(),
                nome_atividade.strip(),
                int(tempo_minutos),
                evidencia.strip() if evidencia else "",
                observacoes.strip() if observacoes else "",
            ),
        )
        return cur.lastrowid


def atualizar_atividade(
    atividade_id: int,
    data_atividade: date,
    nome_atividade: str,
    tempo_minutos: int,
    evidencia: str = "",
    observacoes: str = "",
) -> None:
    """Atualiza uma atividade existente pelo ID."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE atividades
            SET data = ?,
                nome_atividade = ?,
                tempo_minutos = ?,
                evidencia = ?,
                observacoes = ?,
                atualizado_em = datetime('now', 'localtime')
            WHERE id = ?;
            """,
            (
                data_atividade.isoformat(),
                nome_atividade.strip(),
                int(tempo_minutos),
                evidencia.strip() if evidencia else "",
                observacoes.strip() if observacoes else "",
                atividade_id,
            ),
        )


def excluir_atividade(atividade_id: int) -> None:
    """Remove uma atividade pelo ID."""
    with get_connection() as conn:
        conn.execute("DELETE FROM atividades WHERE id = ?;", (atividade_id,))


def buscar_atividade_por_id(atividade_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM atividades WHERE id = ?;", (atividade_id,)
        ).fetchone()
        return dict(row) if row else None


def buscar_ultima_atividade() -> Optional[dict]:
    """Retorna a atividade mais recentemente registrada (por id), ou None se não houver nenhuma."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM atividades ORDER BY id DESC LIMIT 1;"
        ).fetchone()
        return dict(row) if row else None


def duplicar_atividade(atividade_id: int) -> Optional[int]:
    """
    Cria uma cópia de uma atividade existente, usando a data de hoje.
    Retorna o ID da nova atividade, ou None se a original não existir.
    """
    original = buscar_atividade_por_id(atividade_id)
    if not original:
        return None
    return criar_atividade(
        data_atividade=date.today(),
        nome_atividade=original["nome_atividade"],
        tempo_minutos=original["tempo_minutos"],
        evidencia=original["evidencia"] or "",
        observacoes=original["observacoes"] or "",
    )


def listar_atividades(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    termo_busca: Optional[str] = None,
) -> pd.DataFrame:
    """
    Lista atividades com filtros opcionais de período e texto
    (busca em nome_atividade e observacoes). Retorna um DataFrame
    já ordenado por data decrescente.
    """
    query = "SELECT * FROM atividades WHERE 1=1"
    params: list = []

    if data_inicio:
        query += " AND data >= ?"
        params.append(data_inicio.isoformat())
    if data_fim:
        query += " AND data <= ?"
        params.append(data_fim.isoformat())
    if termo_busca:
        query += " AND (nome_atividade LIKE ? OR observacoes LIKE ?)"
        termo_like = f"%{termo_busca}%"
        params.extend([termo_like, termo_like])

    query += " ORDER BY data DESC, id DESC"

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if not df.empty:
        df["data"] = pd.to_datetime(df["data"]).dt.date
    return df


def listar_nomes_atividades_distintos() -> list[str]:
    """
    Retorna a lista de nomes de atividades já usados no histórico,
    ordenados por frequência de uso (mais usados primeiro) e então
    alfabeticamente. Usada para alimentar o autocomplete do campo
    'Atividade' no formulário de registro.
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT nome_atividade, COUNT(*) AS qtd
            FROM atividades
            GROUP BY nome_atividade
            ORDER BY qtd DESC, nome_atividade ASC;
            """
        ).fetchall()
    return [row["nome_atividade"] for row in rows]


def sugerir_atividades(texto_digitado: str, limite: int = 8) -> list[str]:
    """
    Filtra a lista de atividades já usadas no histórico que começam
    com (ou contêm) o texto digitado, para alimentar o autocomplete.
    Comparação é case-insensitive.
    """
    if not texto_digitado:
        return []

    texto_lower = texto_digitado.strip().lower()
    nomes = listar_nomes_atividades_distintos()

    # Prioriza nomes que começam com o texto digitado, depois os que apenas contêm
    comeca_com = [n for n in nomes if n.lower().startswith(texto_lower)]
    contem = [n for n in nomes if texto_lower in n.lower() and n not in comeca_com]

    return (comeca_com + contem)[:limite]


# --------------------------------------------------------------------------
# Configurações (jornada diária, diretórios)
# --------------------------------------------------------------------------


def _obter_configuracao(chave: str, valor_padrao: str) -> str:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT valor FROM configuracoes WHERE chave = ?;", (chave,)
        ).fetchone()
        return row["valor"] if row else valor_padrao


def _definir_configuracao(chave: str, valor: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO configuracoes (chave, valor) VALUES (?, ?)
            ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor;
            """,
            (chave, valor),
        )


def obter_jornada_diaria_horas() -> int:
    return int(_obter_configuracao("jornada_diaria_horas", "8"))


def definir_jornada_diaria_horas(horas: int) -> None:
    _definir_configuracao("jornada_diaria_horas", str(horas))


def obter_dir_relatorios() -> str:
    return _obter_configuracao("dir_relatorios", str(DEFAULT_RELATORIOS_DIR))


def definir_dir_relatorios(caminho: str) -> None:
    _definir_configuracao("dir_relatorios", caminho)


def obter_dir_backups() -> str:
    return _obter_configuracao("dir_backups", str(DEFAULT_BACKUPS_DIR))


def definir_dir_backups(caminho: str) -> None:
    _definir_configuracao("dir_backups", caminho)


# --------------------------------------------------------------------------
# Agregações e resumos
# --------------------------------------------------------------------------


def minutos_para_horas_str(minutos: float) -> str:
    """Converte minutos em uma string 'Hh Mmin' legível."""
    minutos = int(round(minutos))
    horas, resto = divmod(minutos, 60)
    return f"{horas}h {resto:02d}min"


def resumo_periodo(df: pd.DataFrame) -> dict:
    """
    Recebe um DataFrame de atividades (já filtrado pelo período desejado)
    e retorna totais agregados: minutos totais, horas totais e nº de atividades.
    """
    if df.empty:
        return {"total_minutos": 0, "total_horas_str": "0h 00min", "qtd_atividades": 0}

    total_minutos = df["tempo_minutos"].sum()
    return {
        "total_minutos": int(total_minutos),
        "total_horas_str": minutos_para_horas_str(total_minutos),
        "qtd_atividades": len(df),
    }


def percentual_meta(total_minutos: float, jornada_horas: int, dias: int = 1) -> float:
    """
    Calcula o percentual atingido da meta, considerando a jornada diária
    multiplicada pela quantidade de dias do período analisado.
    """
    meta_minutos = jornada_horas * 60 * max(dias, 1)
    if meta_minutos <= 0:
        return 0.0
    return round((total_minutos / meta_minutos) * 100, 1)


def resumo_diario(dia: date) -> dict:
    df = listar_atividades(data_inicio=dia, data_fim=dia)
    resumo = resumo_periodo(df)
    jornada = obter_jornada_diaria_horas()
    resumo["percentual_meta"] = percentual_meta(resumo["total_minutos"], jornada, dias=1)
    resumo["meta_horas"] = jornada
    return resumo


def resumo_semanal(dia_referencia: date) -> dict:
    """Resume a semana (segunda a domingo) que contém dia_referencia."""
    inicio_semana = dia_referencia - timedelta(days=dia_referencia.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    df = listar_atividades(data_inicio=inicio_semana, data_fim=fim_semana)
    resumo = resumo_periodo(df)
    jornada = obter_jornada_diaria_horas()
    dias_uteis = 5  # considera jornada de seg-sex para a meta semanal
    resumo["percentual_meta"] = percentual_meta(resumo["total_minutos"], jornada, dias=dias_uteis)
    resumo["meta_horas"] = jornada * dias_uteis
    resumo["inicio"] = inicio_semana
    resumo["fim"] = fim_semana
    return resumo


def resumo_mensal(ano: int, mes: int) -> dict:
    inicio_mes = date(ano, mes, 1)
    if mes == 12:
        fim_mes = date(ano, 12, 31)
    else:
        fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)

    df = listar_atividades(data_inicio=inicio_mes, data_fim=fim_mes)
    resumo = resumo_periodo(df)
    jornada = obter_jornada_diaria_horas()

    # Conta apenas dias úteis (segunda a sexta) no mês para a meta
    dias_uteis = sum(
        1
        for n in range((fim_mes - inicio_mes).days + 1)
        if (inicio_mes + timedelta(days=n)).weekday() < 5
    )
    resumo["percentual_meta"] = percentual_meta(resumo["total_minutos"], jornada, dias=dias_uteis)
    resumo["meta_horas"] = jornada * dias_uteis
    resumo["inicio"] = inicio_mes
    resumo["fim"] = fim_mes
    return resumo


def trimestre_para_periodo(ano: int, trimestre: int) -> tuple[date, date]:
    """trimestre: 1 a 4. Retorna (data_inicio, data_fim)."""
    mes_inicio = (trimestre - 1) * 3 + 1
    inicio = date(ano, mes_inicio, 1)
    mes_fim = mes_inicio + 2
    if mes_fim == 12:
        fim = date(ano, 12, 31)
    else:
        fim = date(ano, mes_fim + 1, 1) - timedelta(days=1)
    return inicio, fim


def semestre_para_periodo(ano: int, semestre: int) -> tuple[date, date]:
    """semestre: 1 ou 2. Retorna (data_inicio, data_fim)."""
    if semestre == 1:
        return date(ano, 1, 1), date(ano, 6, 30)
    return date(ano, 7, 1), date(ano, 12, 31)


# --------------------------------------------------------------------------
# Importação / Exportação
# --------------------------------------------------------------------------

COLUNAS_EXPORT = [
    "data",
    "nome_atividade",
    "tempo_minutos",
    "evidencia",
    "observacoes",
]


def exportar_para_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara um DataFrame de atividades para exportação (colunas e nomes amigáveis)."""
    if df.empty:
        return pd.DataFrame(columns=["Data", "Atividade", "Minutos", "Horas", "Evidência", "Observações"])

    export_df = df.copy()
    export_df["Horas"] = export_df["tempo_minutos"].apply(minutos_para_horas_str)
    export_df = export_df.rename(
        columns={
            "data": "Data",
            "nome_atividade": "Atividade",
            "tempo_minutos": "Minutos",
            "evidencia": "Evidência",
            "observacoes": "Observações",
        }
    )
    return export_df[["Data", "Atividade", "Minutos", "Horas", "Evidência", "Observações"]]


def importar_de_dataframe(df_importado: pd.DataFrame) -> tuple[int, list[str]]:
    """
    Importa atividades a partir de um DataFrame (lido de um Excel).
    Espera colunas (case-insensitive, com ou sem acento):
    Data, Atividade/Nome da atividade, Minutos/Tempo gasto, Evidência, Observações.

    Retorna (quantidade_importada, lista_de_erros).
    """
    colunas_normalizadas = {
        c: c.strip().lower().replace("á", "a").replace("ê", "e").replace("ã", "a")
        for c in df_importado.columns
    }
    df_importado = df_importado.rename(columns=colunas_normalizadas)

    mapeamento_possiveis = {
        "data": ["data"],
        "nome_atividade": ["atividade", "nome da atividade", "nome_atividade"],
        "tempo_minutos": ["minutos", "tempo gasto", "tempo gasto (em minutos)", "tempo_minutos"],
        "evidencia": ["evidencia", "evidência"],
        "observacoes": ["observacoes", "observações"],
    }

    coluna_real = {}
    for campo, alternativas in mapeamento_possiveis.items():
        for alt in alternativas:
            if alt in df_importado.columns:
                coluna_real[campo] = alt
                break

    erros = []
    if "data" not in coluna_real or "nome_atividade" not in coluna_real or "tempo_minutos" not in coluna_real:
        erros.append(
            "Planilha não contém as colunas obrigatórias (Data, Atividade, Minutos)."
        )
        return 0, erros

    importados = 0
    for idx, linha in df_importado.iterrows():
        try:
            data_valor = pd.to_datetime(linha[coluna_real["data"]]).date()
            nome = str(linha[coluna_real["nome_atividade"]]).strip()
            minutos = int(float(linha[coluna_real["tempo_minutos"]]))
            evidencia = str(linha[coluna_real.get("evidencia", "")]).strip() if "evidencia" in coluna_real else ""
            observ = str(linha[coluna_real.get("observacoes", "")]).strip() if "observacoes" in coluna_real else ""

            if evidencia.lower() == "nan":
                evidencia = ""
            if observ.lower() == "nan":
                observ = ""

            if not nome or minutos <= 0:
                erros.append(f"Linha {idx + 2}: dados inválidos (nome vazio ou minutos <= 0).")
                continue

            criar_atividade(data_valor, nome, minutos, evidencia, observ)
            importados += 1
        except Exception as exc:  # noqa: BLE001
            erros.append(f"Linha {idx + 2}: erro ao importar ({exc}).")

    return importados, erros
