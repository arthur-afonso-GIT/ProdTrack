"""
ui/reports_frame.py
Tela Relatórios — geração de PDF (diário, mensal, trimestral, semestral)
e exportação Excel do período selecionado. Sem gráficos: o foco é
documentação para entrega/comprovação do trabalho realizado.
"""

from datetime import date, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

import models
from services import report_generator, excel_service
from ui import theme

NOMES_MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


class ReportsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.BG, **kwargs)

        self._tipo_var = ctk.StringVar(value="Diário")
        self._construir_layout()
        self._atualizar_campos_periodo()

    def _construir_layout(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=theme.PAD_PAGE, pady=theme.PAD_PAGE)

        ctk.CTkLabel(
            container, text="RELATÓRIOS", font=theme.FONT_SECTION, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 10))

        # Seletor de tipo de relatório
        seletor = ctk.CTkSegmentedButton(
            container,
            values=["Diário", "Mensal", "Trimestral", "Semestral"],
            variable=self._tipo_var,
            command=lambda _: self._atualizar_campos_periodo(),
            fg_color=theme.BG_CARD,
            selected_color=theme.ACCENT,
            selected_hover_color=theme.ACCENT_HOVER,
            unselected_color=theme.BG_CARD,
            text_color=theme.TEXT_PRIMARY,
            font=theme.FONT_BODY,
        )
        seletor.pack(fill="x", pady=(0, theme.PAD_SECTION))

        # Card com os campos de período (muda de acordo com o tipo selecionado)
        self.card_periodo = ctk.CTkFrame(
            container, fg_color=theme.BG_CARD, border_width=1, border_color=theme.BORDER, corner_radius=theme.RADIUS
        )
        self.card_periodo.pack(fill="x", pady=(0, theme.PAD_SECTION))
        self.frame_campos_periodo = ctk.CTkFrame(self.card_periodo, fg_color="transparent")
        self.frame_campos_periodo.pack(fill="x", padx=20, pady=18)

        # Resumo do período (Horas / Meta / %)
        self.frame_resumo = ctk.CTkFrame(container, fg_color="transparent")
        self.frame_resumo.pack(fill="x", pady=(0, theme.PAD_SECTION))

        # Botões de ação
        frame_botoes = ctk.CTkFrame(container, fg_color="transparent")
        frame_botoes.pack(fill="x")
        frame_botoes.grid_columnconfigure((0, 1), weight=1)

        self.btn_pdf = ctk.CTkButton(
            frame_botoes, text="📄 Gerar PDF", command=self._gerar_pdf, **theme.estilo_botao_primario(),
        )
        self.btn_pdf.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.btn_excel = ctk.CTkButton(
            frame_botoes, text="📊 Exportar Excel", command=self._exportar_excel, **theme.estilo_botao_secundario(),
        )
        self.btn_excel.configure(height=42)
        self.btn_excel.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.label_status = ctk.CTkLabel(
            container, text="", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY
        )
        self.label_status.pack(anchor="w", pady=(10, 0))

    # ------------------------------------------------------------------
    # Campos de período — mudam de acordo com o tipo de relatório
    # ------------------------------------------------------------------

    def _limpar_campos_periodo(self):
        for widget in self.frame_campos_periodo.winfo_children():
            widget.destroy()

    def _atualizar_campos_periodo(self):
        self._limpar_campos_periodo()
        tipo = self._tipo_var.get()
        hoje = date.today()

        if tipo == "Diário":
            ctk.CTkLabel(self.frame_campos_periodo, text="Dia", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
            self.entry_dia = ctk.CTkEntry(self.frame_campos_periodo, **theme.estilo_entry())
            self.entry_dia.pack(fill="x", pady=(2, 0))
            self.entry_dia.insert(0, hoje.strftime("%d/%m/%Y"))

        elif tipo == "Mensal":
            linha = ctk.CTkFrame(self.frame_campos_periodo, fg_color="transparent")
            linha.pack(fill="x")
            linha.grid_columnconfigure((0, 1), weight=1)

            bloco_ano = ctk.CTkFrame(linha, fg_color="transparent")
            bloco_ano.grid(row=0, column=0, sticky="ew", padx=(0, 8))
            ctk.CTkLabel(bloco_ano, text="Ano", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
            self.entry_ano = ctk.CTkEntry(bloco_ano, **theme.estilo_entry())
            self.entry_ano.pack(fill="x", pady=(2, 0))
            self.entry_ano.insert(0, str(hoje.year))

            bloco_mes = ctk.CTkFrame(linha, fg_color="transparent")
            bloco_mes.grid(row=0, column=1, sticky="ew", padx=(8, 0))
            ctk.CTkLabel(bloco_mes, text="Mês", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
            self.combo_mes = ctk.CTkComboBox(
                bloco_mes, values=NOMES_MESES, **{k: v for k, v in theme.estilo_entry().items() if k != "border_width"},
                state="readonly",
            )
            self.combo_mes.pack(fill="x", pady=(2, 0))
            self.combo_mes.set(NOMES_MESES[hoje.month - 1])

        elif tipo == "Trimestral":
            linha = ctk.CTkFrame(self.frame_campos_periodo, fg_color="transparent")
            linha.pack(fill="x")
            linha.grid_columnconfigure((0, 1), weight=1)

            bloco_ano = ctk.CTkFrame(linha, fg_color="transparent")
            bloco_ano.grid(row=0, column=0, sticky="ew", padx=(0, 8))
            ctk.CTkLabel(bloco_ano, text="Ano", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
            self.entry_ano = ctk.CTkEntry(bloco_ano, **theme.estilo_entry())
            self.entry_ano.pack(fill="x", pady=(2, 0))
            self.entry_ano.insert(0, str(hoje.year))

            bloco_tri = ctk.CTkFrame(linha, fg_color="transparent")
            bloco_tri.grid(row=0, column=1, sticky="ew", padx=(8, 0))
            ctk.CTkLabel(bloco_tri, text="Trimestre", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
            self.combo_trimestre = ctk.CTkComboBox(
                bloco_tri, values=["1º trimestre", "2º trimestre", "3º trimestre", "4º trimestre"],
                **{k: v for k, v in theme.estilo_entry().items() if k != "border_width"}, state="readonly",
            )
            self.combo_trimestre.pack(fill="x", pady=(2, 0))
            self.combo_trimestre.set("1º trimestre")

        else:  # Semestral
            linha = ctk.CTkFrame(self.frame_campos_periodo, fg_color="transparent")
            linha.pack(fill="x")
            linha.grid_columnconfigure((0, 1), weight=1)

            bloco_ano = ctk.CTkFrame(linha, fg_color="transparent")
            bloco_ano.grid(row=0, column=0, sticky="ew", padx=(0, 8))
            ctk.CTkLabel(bloco_ano, text="Ano", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
            self.entry_ano = ctk.CTkEntry(bloco_ano, **theme.estilo_entry())
            self.entry_ano.pack(fill="x", pady=(2, 0))
            self.entry_ano.insert(0, str(hoje.year))

            bloco_sem = ctk.CTkFrame(linha, fg_color="transparent")
            bloco_sem.grid(row=0, column=1, sticky="ew", padx=(8, 0))
            ctk.CTkLabel(bloco_sem, text="Semestre", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
            self.combo_semestre = ctk.CTkComboBox(
                bloco_sem, values=["1º semestre", "2º semestre"],
                **{k: v for k, v in theme.estilo_entry().items() if k != "border_width"}, state="readonly",
            )
            self.combo_semestre.pack(fill="x", pady=(2, 0))
            self.combo_semestre.set("1º semestre")

        self._atualizar_resumo()

    # ------------------------------------------------------------------
    # Resolução do período selecionado
    # ------------------------------------------------------------------

    def _resolver_periodo(self):
        """
        Lê os campos atuais e retorna (data_inicio, data_fim, titulo, dias_meta),
        ou levanta ValueError com mensagem amigável se algo estiver inválido.
        """
        from datetime import datetime

        tipo = self._tipo_var.get()

        if tipo == "Diário":
            texto = self.entry_dia.get().strip()
            try:
                dia = datetime.strptime(texto, "%d/%m/%Y").date()
            except ValueError:
                raise ValueError("Data inválida. Use o formato dd/mm/aaaa.")
            return dia, dia, f"Relatório Diário — {dia.strftime('%d/%m/%Y')}", 1

        try:
            ano = int(self.entry_ano.get().strip())
        except ValueError:
            raise ValueError("Ano inválido.")

        if tipo == "Mensal":
            mes = NOMES_MESES.index(self.combo_mes.get()) + 1
            ref = models.resumo_mensal(ano, mes)
            dias_meta = sum(
                1 for n in range((ref["fim"] - ref["inicio"]).days + 1)
                if (ref["inicio"] + timedelta(days=n)).weekday() < 5
            )
            return ref["inicio"], ref["fim"], f"Relatório Mensal — {NOMES_MESES[mes - 1]}/{ano}", dias_meta

        if tipo == "Trimestral":
            trimestre = int(self.combo_trimestre.get()[0])
            inicio, fim = models.trimestre_para_periodo(ano, trimestre)
            dias_meta = sum(
                1 for n in range((fim - inicio).days + 1) if (inicio + timedelta(days=n)).weekday() < 5
            )
            return inicio, fim, f"Relatório Trimestral — {trimestre}º Trim/{ano}", dias_meta

        # Semestral
        semestre = int(self.combo_semestre.get()[0])
        inicio, fim = models.semestre_para_periodo(ano, semestre)
        dias_meta = sum(
            1 for n in range((fim - inicio).days + 1) if (inicio + timedelta(days=n)).weekday() < 5
        )
        return inicio, fim, f"Relatório Semestral — {semestre}º Sem/{ano}", dias_meta

    # ------------------------------------------------------------------
    # Resumo do período (Horas / Meta / %)
    # ------------------------------------------------------------------

    def _atualizar_resumo(self):
        for widget in self.frame_resumo.winfo_children():
            widget.destroy()

        try:
            data_inicio, data_fim, _, dias_meta = self._resolver_periodo()
        except ValueError:
            return

        jornada = models.obter_jornada_diaria_horas()
        df_periodo = models.listar_atividades(data_inicio=data_inicio, data_fim=data_fim)
        resumo = models.resumo_periodo(df_periodo)
        percentual = models.percentual_meta(resumo["total_minutos"], jornada, dias=dias_meta)

        linha = ctk.CTkFrame(self.frame_resumo, fg_color="transparent")
        linha.pack(fill="x")

        for label, valor, cor in [
            ("Horas registradas", resumo["total_horas_str"], theme.TEXT_PRIMARY),
            ("Meta do período", f"{jornada * dias_meta}h", theme.TEXT_PRIMARY),
            ("% atingido", f"{percentual}%", theme.SUCCESS if percentual >= 100 else theme.TEXT_PRIMARY),
        ]:
            bloco = ctk.CTkFrame(linha, fg_color="transparent")
            bloco.pack(side="left", padx=(0, 28))
            ctk.CTkLabel(bloco, text=label, font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
            ctk.CTkLabel(bloco, text=valor, font=theme.FONT_BIG_NUMBER, text_color=cor).pack(anchor="w")

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------

    def _gerar_pdf(self):
        try:
            data_inicio, data_fim, titulo, dias_meta = self._resolver_periodo()
        except ValueError as exc:
            messagebox.showerror("ProdTrack", str(exc))
            return

        jornada = models.obter_jornada_diaria_horas()
        df_periodo = models.listar_atividades(data_inicio=data_inicio, data_fim=data_fim)

        try:
            caminho = report_generator.gerar_relatorio_pdf(
                df=df_periodo, titulo=titulo, data_inicio=data_inicio,
                data_fim=data_fim, jornada_horas=jornada, dias_meta=dias_meta,
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("ProdTrack", f"Erro ao gerar PDF: {exc}")
            return

        self.label_status.configure(text=f"PDF gerado em: {caminho}")
        messagebox.showinfo("ProdTrack", f"Relatório gerado com sucesso:\n{caminho}")

    def _exportar_excel(self):
        try:
            data_inicio, data_fim, _, _ = self._resolver_periodo()
        except ValueError as exc:
            messagebox.showerror("ProdTrack", str(exc))
            return

        df_periodo = models.listar_atividades(data_inicio=data_inicio, data_fim=data_fim)

        if df_periodo.empty:
            messagebox.showinfo("ProdTrack", "Nenhuma atividade no período selecionado.")
            return

        sugestao_nome = f"prodtrack_{data_inicio.strftime('%Y%m%d')}_{data_fim.strftime('%Y%m%d')}.xlsx"
        destino = filedialog.asksaveasfilename(
            title="Salvar Excel", defaultextension=".xlsx",
            initialfile=sugestao_nome, filetypes=[("Planilha Excel", "*.xlsx")],
        )
        if not destino:
            return

        try:
            caminho = excel_service.exportar_atividades_para_excel(df_periodo, Path(destino))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("ProdTrack", f"Erro ao exportar Excel: {exc}")
            return

        self.label_status.configure(text=f"Excel exportado em: {caminho}")
        messagebox.showinfo("ProdTrack", f"Excel exportado com sucesso:\n{caminho}")

    def atualizar(self):
        """Chamada ao entrar na tela."""
        self._atualizar_resumo()
