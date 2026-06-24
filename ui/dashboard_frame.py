"""
ui/dashboard_frame.py
Tela Início — a tela principal do ProdTrack.

Contém, de cima para baixo:
1. Resumo do dia (Hoje / Meta / Faltam + barra de progresso) — uma linha só.
2. Formulário de registro rápido de atividade (o elemento central da tela).
3. Lista das últimas atividades registradas, com editar/duplicar/excluir.

Filosofia: o usuário deve conseguir registrar uma atividade em menos de
10 segundos, sem precisar navegar para nenhum outro lugar.
"""

from datetime import date, datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk

import models
from ui import theme
from ui.autocomplete_entry import AutocompleteEntry


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.BG, **kwargs)

        self._evidencia_arquivo_path: str = ""  # caminho de arquivo anexado (se houver)
        self._editando_id: int | None = None     # id da atividade em edição inline, se houver

        self._construir_layout()
        self.atualizar()

    # ------------------------------------------------------------------
    # Construção da tela (chamada uma única vez)
    # ------------------------------------------------------------------

    def _construir_layout(self):
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=theme.PAD_PAGE, pady=theme.PAD_PAGE)
        self._container = container

        self._construir_resumo_dia(container)
        self._construir_formulario(container)
        self._construir_lista_recentes(container)

    def _construir_resumo_dia(self, parent):
        frame_resumo = ctk.CTkFrame(parent, fg_color="transparent")
        frame_resumo.pack(fill="x", pady=(0, theme.PAD_SECTION))

        linha = ctk.CTkFrame(frame_resumo, fg_color="transparent")
        linha.pack(fill="x")

        self._bloco_hoje = self._criar_bloco_metrica(linha, "Hoje")
        self._bloco_hoje.pack(side="left", padx=(0, 28))

        self._bloco_meta = self._criar_bloco_metrica(linha, "Meta")
        self._bloco_meta.pack(side="left", padx=(0, 28))

        self._bloco_faltam = self._criar_bloco_metrica(linha, "Faltam")
        self._bloco_faltam.pack(side="left")

        self._barra_progresso = ctk.CTkProgressBar(
            frame_resumo,
            height=8,
            corner_radius=4,
            progress_color=theme.ACCENT,
            fg_color=theme.BORDER,
        )
        self._barra_progresso.pack(fill="x", pady=(12, 0))
        self._barra_progresso.set(0)

    def _criar_bloco_metrica(self, parent, label: str) -> ctk.CTkFrame:
        """Cria um bloco 'label pequeno em cima / valor grande embaixo' (ex.: Hoje: 4h20m)."""
        bloco = ctk.CTkFrame(parent, fg_color="transparent")
        lbl = ctk.CTkLabel(bloco, text=label, font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY)
        lbl.pack(anchor="w")
        valor = ctk.CTkLabel(bloco, text="—", font=theme.FONT_BIG_NUMBER, text_color=theme.TEXT_PRIMARY)
        valor.pack(anchor="w")
        bloco.valor_label = valor  # referência guardada para atualização posterior
        return bloco

    def _construir_formulario(self, parent):
        secao = ctk.CTkLabel(
            parent, text="REGISTRAR ATIVIDADE", font=theme.FONT_SECTION, text_color=theme.TEXT_SECONDARY
        )
        secao.pack(anchor="w", pady=(0, 8))

        card = ctk.CTkFrame(
            parent, fg_color=theme.BG_CARD, border_width=1, border_color=theme.BORDER, corner_radius=theme.RADIUS
        )
        card.pack(fill="x", pady=(0, theme.PAD_SECTION))

        interno = ctk.CTkFrame(card, fg_color="transparent")
        interno.pack(fill="x", padx=20, pady=18)

        # Linha 1: Data + Tempo gasto (lado a lado, mesma linha — economiza espaço vertical)
        linha1 = ctk.CTkFrame(interno, fg_color="transparent")
        linha1.pack(fill="x", pady=(0, theme.PAD_FIELD))
        linha1.grid_columnconfigure(0, weight=1)
        linha1.grid_columnconfigure(1, weight=1)

        bloco_data = ctk.CTkFrame(linha1, fg_color="transparent")
        bloco_data.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(bloco_data, text="Data", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.entry_data = ctk.CTkEntry(bloco_data, **theme.estilo_entry())
        self.entry_data.pack(fill="x", pady=(2, 0))
        self.entry_data.insert(0, date.today().strftime("%d/%m/%Y"))

        bloco_tempo = ctk.CTkFrame(linha1, fg_color="transparent")
        bloco_tempo.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(
            bloco_tempo, text="Tempo gasto (min)", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w")
        self.entry_tempo = ctk.CTkEntry(bloco_tempo, **theme.estilo_entry())
        self.entry_tempo.pack(fill="x", pady=(2, 0))
        self.entry_tempo.insert(0, "30")

        # Linha 2: Atividade (com autocomplete) + botão "repetir última"
        bloco_atividade = ctk.CTkFrame(interno, fg_color="transparent")
        bloco_atividade.pack(fill="x", pady=(0, theme.PAD_FIELD))

        cabecalho_atividade = ctk.CTkFrame(bloco_atividade, fg_color="transparent")
        cabecalho_atividade.pack(fill="x")
        ctk.CTkLabel(
            cabecalho_atividade, text="Atividade", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY
        ).pack(side="left", anchor="w")

        self.btn_repetir = ctk.CTkButton(
            cabecalho_atividade,
            text="↻ Repetir última",
            command=self._repetir_ultima_atividade,
            fg_color="transparent",
            hover_color=theme.ROW_HOVER,
            text_color=theme.TEXT_SECONDARY,
            font=theme.FONT_SMALL,
            corner_radius=theme.RADIUS,
            width=140,
            height=28,
            anchor="e",
        )
        self.btn_repetir.pack(side="right")

        self.campo_atividade = AutocompleteEntry(
            bloco_atividade,
            fornecedor_sugestoes=lambda texto: models.sugerir_atividades(texto),
            placeholder_text="O que você fez?",
        )
        self.campo_atividade.pack(fill="x", pady=(2, 0))

        # Linha 3: Evidência (link ou arquivo)
        bloco_evidencia = ctk.CTkFrame(interno, fg_color="transparent")
        bloco_evidencia.pack(fill="x", pady=(0, theme.PAD_FIELD))
        ctk.CTkLabel(
            bloco_evidencia, text="Evidência", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w")

        linha_evidencia = ctk.CTkFrame(bloco_evidencia, fg_color="transparent")
        linha_evidencia.pack(fill="x", pady=(2, 0))

        self.entry_evidencia = ctk.CTkEntry(
            linha_evidencia, placeholder_text="Link ou caminho do arquivo", **theme.estilo_entry()
        )
        self.entry_evidencia.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_anexar = ctk.CTkButton(
            linha_evidencia, text="📎 Anexar", command=self._escolher_arquivo_evidencia,
            **theme.estilo_botao_secundario(), width=100,
        )
        self.btn_anexar.pack(side="left")

        # Linha 4: Observações
        bloco_observ = ctk.CTkFrame(interno, fg_color="transparent")
        bloco_observ.pack(fill="x", pady=(0, theme.PAD_FIELD))
        ctk.CTkLabel(
            bloco_observ, text="Observações", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w")
        self.entry_observacoes = ctk.CTkTextbox(
            bloco_observ, height=60, fg_color=theme.BG_CARD, border_width=1,
            border_color=theme.BORDER, corner_radius=theme.RADIUS, font=theme.FONT_BODY,
        )
        self.entry_observacoes.pack(fill="x", pady=(2, 0))

        # Botão salvar — grande, largura total
        self.btn_salvar = ctk.CTkButton(
            interno, text="Salvar atividade", command=self._salvar_atividade,
            **theme.estilo_botao_primario(),
        )
        self.btn_salvar.pack(fill="x", pady=(8, 0))

        # Atalho de teclado: Ctrl+Enter salva de qualquer campo do formulário
        for widget in (self.entry_data, self.entry_tempo, self.entry_evidencia):
            widget.bind("<Control-Return>", lambda e: self._salvar_atividade())

    def _construir_lista_recentes(self, parent):
        secao = ctk.CTkLabel(
            parent, text="ATIVIDADES RECENTES", font=theme.FONT_SECTION, text_color=theme.TEXT_SECONDARY
        )
        secao.pack(anchor="w", pady=(0, 8))

        self.frame_lista = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame_lista.pack(fill="x")

    # ------------------------------------------------------------------
    # Atualização de dados (chamada ao abrir a tela ou após qualquer mudança)
    # ------------------------------------------------------------------

    def atualizar(self):
        self._atualizar_resumo_dia()
        self._atualizar_lista_recentes()

    def _atualizar_resumo_dia(self):
        resumo = models.resumo_diario(date.today())
        total_min = resumo["total_minutos"]
        meta_horas = resumo["meta_horas"]
        meta_min = meta_horas * 60
        faltam_min = max(meta_min - total_min, 0)
        atingiu_meta = total_min >= meta_min

        self._bloco_hoje.valor_label.configure(text=resumo["total_horas_str"])
        self._bloco_meta.valor_label.configure(text=f"{meta_horas}h")

        if atingiu_meta:
            self._bloco_faltam.valor_label.configure(text="Meta atingida 🎉", text_color=theme.SUCCESS)
        else:
            self._bloco_faltam.valor_label.configure(
                text=models.minutos_para_horas_str(faltam_min), text_color=theme.TEXT_PRIMARY
            )

        progresso = min(total_min / meta_min, 1.0) if meta_min > 0 else 0
        self._barra_progresso.set(progresso)

    def _atualizar_lista_recentes(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        df = models.listar_atividades().head(8)

        if df.empty:
            ctk.CTkLabel(
                self.frame_lista, text="Nenhuma atividade registrada ainda. Comece acima ⬆️",
                font=theme.FONT_BODY, text_color=theme.TEXT_SECONDARY,
            ).pack(anchor="w", pady=8)
            return

        for _, row in df.iterrows():
            self._criar_linha_atividade(self.frame_lista, row)

    def _criar_linha_atividade(self, parent, row):
        linha = ctk.CTkFrame(parent, fg_color="transparent")
        linha.pack(fill="x")

        # Borda inferior sutil simulada com um frame fino
        separador = ctk.CTkFrame(linha, fg_color=theme.BORDER, height=1)

        info = ctk.CTkFrame(linha, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, pady=10)

        ctk.CTkLabel(
            info, text=row["nome_atividade"], font=theme.FONT_BODY_BOLD,
            text_color=theme.TEXT_PRIMARY, anchor="w",
        ).pack(anchor="w")

        meta_texto = f"{row['data'].strftime('%d/%m')} · {models.minutos_para_horas_str(row['tempo_minutos'])}"
        if row.get("evidencia"):
            meta_texto += f" · 🔗 {row['evidencia']}"

        ctk.CTkLabel(
            info, text=meta_texto, font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY, anchor="w",
        ).pack(anchor="w")

        acoes = ctk.CTkFrame(linha, fg_color="transparent")
        acoes.pack(side="right", pady=10)

        atividade_id = int(row["id"])

        ctk.CTkButton(
            acoes, text="✏️", command=lambda: self._editar_atividade(atividade_id), **theme.estilo_botao_icone()
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            acoes, text="⧉", command=lambda: self._duplicar_atividade(atividade_id), **theme.estilo_botao_icone()
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            acoes, text="🗑️", command=lambda: self._confirmar_exclusao(atividade_id), **theme.estilo_botao_icone()
        ).pack(side="left", padx=2)

        separador.pack(fill="x", pady=(0, 0))

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------

    def _escolher_arquivo_evidencia(self):
        caminho = filedialog.askopenfilename(title="Selecionar arquivo de evidência")
        if caminho:
            self._evidencia_arquivo_path = caminho
            self.entry_evidencia.delete(0, "end")
            self.entry_evidencia.insert(0, caminho)

    def _repetir_ultima_atividade(self):
        ultima = models.buscar_ultima_atividade()
        if not ultima:
            messagebox.showinfo("ProdTrack", "Ainda não há nenhuma atividade registrada.")
            return

        self.campo_atividade.set(ultima["nome_atividade"])
        self.entry_evidencia.delete(0, "end")
        self.entry_evidencia.insert(0, ultima["evidencia"] or "")
        self.entry_tempo.focus()
        self.entry_tempo.select_range(0, "end")

    def _parse_data(self, texto: str) -> date | None:
        texto = texto.strip()
        for formato in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(texto, formato).date()
            except ValueError:
                continue
        return None

    def _limpar_formulario(self):
        self.entry_data.delete(0, "end")
        self.entry_data.insert(0, date.today().strftime("%d/%m/%Y"))
        self.campo_atividade.set("")
        self.entry_tempo.delete(0, "end")
        self.entry_tempo.insert(0, "30")
        self.entry_evidencia.delete(0, "end")
        self.entry_observacoes.delete("1.0", "end")
        self._evidencia_arquivo_path = ""

    def _salvar_atividade(self):
        data_atividade = self._parse_data(self.entry_data.get())
        if data_atividade is None:
            messagebox.showerror("ProdTrack", "Data inválida. Use o formato dd/mm/aaaa.")
            return

        nome_atividade = self.campo_atividade.get().strip()
        if not nome_atividade:
            messagebox.showerror("ProdTrack", "Informe o nome da atividade.")
            self.campo_atividade.focus()
            return

        try:
            tempo_minutos = int(self.entry_tempo.get().strip())
            if tempo_minutos <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("ProdTrack", "Tempo gasto deve ser um número inteiro maior que zero.")
            self.entry_tempo.focus()
            return

        evidencia = self.entry_evidencia.get().strip()
        observacoes = self.entry_observacoes.get("1.0", "end").strip()

        models.criar_atividade(
            data_atividade=data_atividade,
            nome_atividade=nome_atividade,
            tempo_minutos=tempo_minutos,
            evidencia=evidencia,
            observacoes=observacoes,
        )

        self._limpar_formulario()
        self.atualizar()
        self.campo_atividade.focus()

    def _editar_atividade(self, atividade_id: int):
        atividade = models.buscar_atividade_por_id(atividade_id)
        if not atividade:
            return
        EditarAtividadeDialog(self, atividade, on_salvo=self.atualizar)

    def _duplicar_atividade(self, atividade_id: int):
        models.duplicar_atividade(atividade_id)
        self.atualizar()

    def _confirmar_exclusao(self, atividade_id: int):
        atividade = models.buscar_atividade_por_id(atividade_id)
        if not atividade:
            return
        confirmou = messagebox.askyesno(
            "Excluir atividade", f"Excluir a atividade \"{atividade['nome_atividade']}\"?"
        )
        if confirmou:
            models.excluir_atividade(atividade_id)
            self.atualizar()


class EditarAtividadeDialog(ctk.CTkToplevel):
    """Janela modal simples para editar uma atividade existente."""

    def __init__(self, master, atividade: dict, on_salvo):
        super().__init__(master)
        self._atividade = atividade
        self._on_salvo = on_salvo

        self.title("Editar atividade")
        self.geometry("420x460")
        self.configure(fg_color=theme.BG)
        self.resizable(False, False)
        self.grab_set()  # foco modal

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="Data", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.entry_data = ctk.CTkEntry(container, **theme.estilo_entry())
        self.entry_data.pack(fill="x", pady=(2, 10))
        self.entry_data.insert(0, datetime.strptime(atividade["data"], "%Y-%m-%d").strftime("%d/%m/%Y"))

        ctk.CTkLabel(container, text="Atividade", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.entry_nome = ctk.CTkEntry(container, **theme.estilo_entry())
        self.entry_nome.pack(fill="x", pady=(2, 10))
        self.entry_nome.insert(0, atividade["nome_atividade"])

        ctk.CTkLabel(
            container, text="Tempo gasto (min)", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w")
        self.entry_tempo = ctk.CTkEntry(container, **theme.estilo_entry())
        self.entry_tempo.pack(fill="x", pady=(2, 10))
        self.entry_tempo.insert(0, str(atividade["tempo_minutos"]))

        ctk.CTkLabel(container, text="Evidência", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.entry_evidencia = ctk.CTkEntry(container, **theme.estilo_entry())
        self.entry_evidencia.pack(fill="x", pady=(2, 10))
        self.entry_evidencia.insert(0, atividade["evidencia"] or "")

        ctk.CTkLabel(container, text="Observações", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.entry_observ = ctk.CTkTextbox(
            container, height=70, fg_color=theme.BG_CARD, border_width=1,
            border_color=theme.BORDER, corner_radius=theme.RADIUS, font=theme.FONT_BODY,
        )
        self.entry_observ.pack(fill="x", pady=(2, 14))
        self.entry_observ.insert("1.0", atividade["observacoes"] or "")

        linha_botoes = ctk.CTkFrame(container, fg_color="transparent")
        linha_botoes.pack(fill="x")

        ctk.CTkButton(
            linha_botoes, text="Cancelar", command=self.destroy, **theme.estilo_botao_secundario()
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            linha_botoes, text="Salvar alterações", command=self._salvar, **theme.estilo_botao_primario()
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))

    def _parse_data(self, texto: str) -> date | None:
        texto = texto.strip()
        for formato in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(texto, formato).date()
            except ValueError:
                continue
        return None

    def _salvar(self):
        nova_data = self._parse_data(self.entry_data.get())
        if nova_data is None:
            messagebox.showerror("ProdTrack", "Data inválida. Use o formato dd/mm/aaaa.")
            return

        nome = self.entry_nome.get().strip()
        if not nome:
            messagebox.showerror("ProdTrack", "Informe o nome da atividade.")
            return

        try:
            tempo = int(self.entry_tempo.get().strip())
            if tempo <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("ProdTrack", "Tempo gasto deve ser um número inteiro maior que zero.")
            return

        models.atualizar_atividade(
            self._atividade["id"],
            nova_data,
            nome,
            tempo,
            self.entry_evidencia.get().strip(),
            self.entry_observ.get("1.0", "end").strip(),
        )

        self.destroy()
        self._on_salvo()
