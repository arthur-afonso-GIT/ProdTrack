"""
ui/history_frame.py
Tela Histórico — filtros por data/atividade + tabela paginada,
com ações de editar, duplicar e excluir por linha.
"""

from datetime import date, datetime, timedelta
from tkinter import messagebox

import customtkinter as ctk

import models
from ui import theme

POR_PAGINA = 15


class HistoryFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.BG, **kwargs)

        self._pagina_atual = 1
        self._df_atual = None

        self._construir_layout()

    def _construir_layout(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=theme.PAD_PAGE, pady=theme.PAD_PAGE)

        ctk.CTkLabel(
            container, text="HISTÓRICO", font=theme.FONT_SECTION, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 10))

        self._construir_filtros(container)

        self.label_total = ctk.CTkLabel(
            container, text="", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY
        )
        self.label_total.pack(anchor="w", pady=(4, 10))

        self.frame_tabela = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.frame_tabela.pack(fill="both", expand=True)

        self._construir_paginacao(container)

    def _construir_filtros(self, parent):
        frame_filtros = ctk.CTkFrame(parent, fg_color="transparent")
        frame_filtros.pack(fill="x")
        frame_filtros.grid_columnconfigure((0, 1, 2), weight=1)

        bloco_de = ctk.CTkFrame(frame_filtros, fg_color="transparent")
        bloco_de.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(bloco_de, text="De", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.entry_data_inicio = ctk.CTkEntry(bloco_de, **theme.estilo_entry())
        self.entry_data_inicio.pack(fill="x", pady=(2, 0))
        self.entry_data_inicio.insert(0, (date.today() - timedelta(days=30)).strftime("%d/%m/%Y"))

        bloco_ate = ctk.CTkFrame(frame_filtros, fg_color="transparent")
        bloco_ate.grid(row=0, column=1, sticky="ew", padx=8)
        ctk.CTkLabel(bloco_ate, text="Até", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.entry_data_fim = ctk.CTkEntry(bloco_ate, **theme.estilo_entry())
        self.entry_data_fim.pack(fill="x", pady=(2, 0))
        self.entry_data_fim.insert(0, date.today().strftime("%d/%m/%Y"))

        bloco_termo = ctk.CTkFrame(frame_filtros, fg_color="transparent")
        bloco_termo.grid(row=0, column=2, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(bloco_termo, text="Atividade", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.entry_termo = ctk.CTkEntry(bloco_termo, placeholder_text="Buscar...", **theme.estilo_entry())
        self.entry_termo.pack(fill="x", pady=(2, 0))
        self.entry_termo.bind("<Return>", lambda e: self.aplicar_filtros())

        self.btn_filtrar = ctk.CTkButton(
            frame_filtros, text="Filtrar", command=self.aplicar_filtros, **theme.estilo_botao_primario(),
        )
        self.btn_filtrar.configure(height=38)
        self.btn_filtrar.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(10, 0))

    def _construir_paginacao(self, parent):
        frame_pag = ctk.CTkFrame(parent, fg_color="transparent")
        frame_pag.pack(fill="x", pady=(10, 0))

        self.btn_anterior = ctk.CTkButton(
            frame_pag, text="‹ Anterior", command=self._pagina_anterior, **theme.estilo_botao_secundario(), width=100,
        )
        self.btn_anterior.pack(side="left")

        self.label_pagina = ctk.CTkLabel(
            frame_pag, text="", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY
        )
        self.label_pagina.pack(side="left", expand=True)

        self.btn_proxima = ctk.CTkButton(
            frame_pag, text="Próxima ›", command=self._pagina_proxima, **theme.estilo_botao_secundario(), width=100,
        )
        self.btn_proxima.pack(side="right")

    def _parse_data(self, texto: str) -> date | None:
        texto = texto.strip()
        for formato in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(texto, formato).date()
            except ValueError:
                continue
        return None

    def atualizar(self):
        """Chamada ao entrar na tela — recarrega com os filtros atuais."""
        self.aplicar_filtros()

    def aplicar_filtros(self):
        data_inicio = self._parse_data(self.entry_data_inicio.get())
        data_fim = self._parse_data(self.entry_data_fim.get())
        termo = self.entry_termo.get().strip() or None

        if self.entry_data_inicio.get().strip() and data_inicio is None:
            messagebox.showerror("ProdTrack", "Data inicial inválida. Use dd/mm/aaaa.")
            return
        if self.entry_data_fim.get().strip() and data_fim is None:
            messagebox.showerror("ProdTrack", "Data final inválida. Use dd/mm/aaaa.")
            return

        self._df_atual = models.listar_atividades(
            data_inicio=data_inicio, data_fim=data_fim, termo_busca=termo
        )
        self._pagina_atual = 1
        self._renderizar_pagina()

    def _total_paginas(self) -> int:
        if self._df_atual is None or self._df_atual.empty:
            return 1
        return max((len(self._df_atual) - 1) // POR_PAGINA + 1, 1)

    def _pagina_anterior(self):
        if self._pagina_atual > 1:
            self._pagina_atual -= 1
            self._renderizar_pagina()

    def _pagina_proxima(self):
        if self._pagina_atual < self._total_paginas():
            self._pagina_atual += 1
            self._renderizar_pagina()

    def _renderizar_pagina(self):
        for widget in self.frame_tabela.winfo_children():
            widget.destroy()

        df = self._df_atual
        if df is None or df.empty:
            self.label_total.configure(text="Nenhum resultado para os filtros aplicados.")
            self.label_pagina.configure(text="")
            return

        total_str = models.minutos_para_horas_str(df["tempo_minutos"].sum())
        self.label_total.configure(text=f"{len(df)} atividade(s) · total {total_str}")

        total_paginas = self._total_paginas()
        self.label_pagina.configure(text=f"Página {self._pagina_atual} de {total_paginas}")
        self.btn_anterior.configure(state="normal" if self._pagina_atual > 1 else "disabled")
        self.btn_proxima.configure(state="normal" if self._pagina_atual < total_paginas else "disabled")

        inicio_idx = (self._pagina_atual - 1) * POR_PAGINA
        df_pagina = df.iloc[inicio_idx: inicio_idx + POR_PAGINA]

        # Cabeçalho da tabela
        cabecalho = ctk.CTkFrame(self.frame_tabela, fg_color="transparent")
        cabecalho.pack(fill="x", pady=(0, 4))
        for texto, largura in [("Data", 90), ("Atividade", 280), ("Tempo", 90), ("Evidência", 200)]:
            ctk.CTkLabel(
                cabecalho, text=texto, font=theme.FONT_SECTION, text_color=theme.TEXT_SECONDARY,
                width=largura, anchor="w",
            ).pack(side="left")
        ctk.CTkLabel(cabecalho, text="", width=110).pack(side="left")  # espaço para botões de ação

        for _, row in df_pagina.iterrows():
            self._criar_linha(row)

    def _criar_linha(self, row):
        linha = ctk.CTkFrame(self.frame_tabela, fg_color="transparent")
        linha.pack(fill="x")

        separador = ctk.CTkFrame(linha, fg_color=theme.BORDER, height=1)

        ctk.CTkLabel(
            linha, text=row["data"].strftime("%d/%m/%Y"), font=theme.FONT_BODY,
            text_color=theme.TEXT_PRIMARY, width=90, anchor="w",
        ).pack(side="left", pady=8)

        ctk.CTkLabel(
            linha, text=row["nome_atividade"], font=theme.FONT_BODY,
            text_color=theme.TEXT_PRIMARY, width=280, anchor="w",
        ).pack(side="left", pady=8)

        ctk.CTkLabel(
            linha, text=models.minutos_para_horas_str(row["tempo_minutos"]), font=theme.FONT_BODY,
            text_color=theme.TEXT_PRIMARY, width=90, anchor="w",
        ).pack(side="left", pady=8)

        evidencia_texto = row["evidencia"] if row.get("evidencia") else "-"
        ctk.CTkLabel(
            linha, text=evidencia_texto, font=theme.FONT_BODY,
            text_color=theme.TEXT_SECONDARY, width=200, anchor="w",
        ).pack(side="left", pady=8)

        acoes = ctk.CTkFrame(linha, fg_color="transparent", width=110)
        acoes.pack(side="left", pady=4)

        atividade_id = int(row["id"])
        ctk.CTkButton(
            acoes, text="✏️", command=lambda: self._editar(atividade_id), **theme.estilo_botao_icone()
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            acoes, text="⧉", command=lambda: self._duplicar(atividade_id), **theme.estilo_botao_icone()
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            acoes, text="🗑️", command=lambda: self._excluir(atividade_id), **theme.estilo_botao_icone()
        ).pack(side="left", padx=2)

        separador.pack(fill="x")

    def _editar(self, atividade_id: int):
        atividade = models.buscar_atividade_por_id(atividade_id)
        if not atividade:
            return
        from ui.dashboard_frame import EditarAtividadeDialog
        EditarAtividadeDialog(self, atividade, on_salvo=self.aplicar_filtros)

    def _duplicar(self, atividade_id: int):
        models.duplicar_atividade(atividade_id)
        self.aplicar_filtros()

    def _excluir(self, atividade_id: int):
        atividade = models.buscar_atividade_por_id(atividade_id)
        if not atividade:
            return
        confirmou = messagebox.askyesno(
            "Excluir atividade", f"Excluir a atividade \"{atividade['nome_atividade']}\"?"
        )
        if confirmou:
            models.excluir_atividade(atividade_id)
            self.aplicar_filtros()
