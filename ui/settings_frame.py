"""
ui/settings_frame.py
Tela Configurações — jornada diária, diretórios padrão de relatórios
e backups, backup manual/restauração, e importação/exportação de
Excel completo (fora do fluxo principal de registro).
"""

from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

import models
from services import backup_service, excel_service
from ui import theme


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.BG, **kwargs)
        self._construir_layout()

    def _construir_layout(self):
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=theme.PAD_PAGE, pady=theme.PAD_PAGE)

        self._secao_jornada(container)
        self._secao_diretorios(container)
        self._secao_excel(container)
        self._secao_backup(container)

    # ------------------------------------------------------------------
    # Jornada diária
    # ------------------------------------------------------------------

    def _secao_jornada(self, parent):
        ctk.CTkLabel(
            parent, text="JORNADA DIÁRIA", font=theme.FONT_SECTION, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 8))

        card = self._novo_card(parent)

        self._jornada_var = ctk.StringVar(value=f"{models.obter_jornada_diaria_horas()}h/dia")
        opcoes = ["6h/dia", "7h/dia", "8h/dia"]

        seletor = ctk.CTkSegmentedButton(
            card, values=opcoes, variable=self._jornada_var,
            command=self._salvar_jornada,
            fg_color=theme.BG, selected_color=theme.ACCENT, selected_hover_color=theme.ACCENT_HOVER,
            unselected_color=theme.BG, text_color=theme.TEXT_PRIMARY, font=theme.FONT_BODY,
        )
        seletor.pack(fill="x", padx=20, pady=18)

    def _salvar_jornada(self, valor: str):
        horas = int(valor.replace("h/dia", ""))
        models.definir_jornada_diaria_horas(horas)

    # ------------------------------------------------------------------
    # Diretórios padrão
    # ------------------------------------------------------------------

    def _secao_diretorios(self, parent):
        ctk.CTkLabel(
            parent, text="DIRETÓRIOS PADRÃO", font=theme.FONT_SECTION, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(theme.PAD_SECTION, 8))

        card = self._novo_card(parent)
        interno = ctk.CTkFrame(card, fg_color="transparent")
        interno.pack(fill="x", padx=20, pady=18)

        # Diretório de relatórios
        ctk.CTkLabel(
            interno, text="Relatórios PDF / Excel", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w")
        linha_rel = ctk.CTkFrame(interno, fg_color="transparent")
        linha_rel.pack(fill="x", pady=(2, 14))
        self.entry_dir_relatorios = ctk.CTkEntry(linha_rel, **theme.estilo_entry())
        self.entry_dir_relatorios.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_dir_relatorios.insert(0, models.obter_dir_relatorios())
        ctk.CTkButton(
            linha_rel, text="Escolher...", command=self._escolher_dir_relatorios,
            **theme.estilo_botao_secundario(), width=110,
        ).pack(side="left")

        # Diretório de backups
        ctk.CTkLabel(
            interno, text="Backups do banco de dados", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w")
        linha_bkp = ctk.CTkFrame(interno, fg_color="transparent")
        linha_bkp.pack(fill="x", pady=(2, 0))
        self.entry_dir_backups = ctk.CTkEntry(linha_bkp, **theme.estilo_entry())
        self.entry_dir_backups.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_dir_backups.insert(0, models.obter_dir_backups())
        ctk.CTkButton(
            linha_bkp, text="Escolher...", command=self._escolher_dir_backups,
            **theme.estilo_botao_secundario(), width=110,
        ).pack(side="left")

    def _escolher_dir_relatorios(self):
        caminho = filedialog.askdirectory(title="Escolher diretório de relatórios")
        if caminho:
            self.entry_dir_relatorios.delete(0, "end")
            self.entry_dir_relatorios.insert(0, caminho)
            models.definir_dir_relatorios(caminho)

    def _escolher_dir_backups(self):
        caminho = filedialog.askdirectory(title="Escolher diretório de backups")
        if caminho:
            self.entry_dir_backups.delete(0, "end")
            self.entry_dir_backups.insert(0, caminho)
            models.definir_dir_backups(caminho)

    # ------------------------------------------------------------------
    # Importar / Exportar Excel (banco completo)
    # ------------------------------------------------------------------

    def _secao_excel(self, parent):
        ctk.CTkLabel(
            parent, text="IMPORTAR / EXPORTAR EXCEL", font=theme.FONT_SECTION, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(theme.PAD_SECTION, 8))

        card = self._novo_card(parent)
        interno = ctk.CTkFrame(card, fg_color="transparent")
        interno.pack(fill="x", padx=20, pady=18)

        linha = ctk.CTkFrame(interno, fg_color="transparent")
        linha.pack(fill="x")
        linha.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            linha, text="⬇️ Exportar tudo", command=self._exportar_tudo, **theme.estilo_botao_secundario(),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            linha, text="⬆️ Importar planilha", command=self._importar_planilha, **theme.estilo_botao_secundario(),
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.label_status_excel = ctk.CTkLabel(
            interno, text="", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY
        )
        self.label_status_excel.pack(anchor="w", pady=(10, 0))

    def _exportar_tudo(self):
        df = models.listar_atividades()
        if df.empty:
            messagebox.showinfo("ProdTrack", "Não há atividades para exportar.")
            return

        destino = filedialog.asksaveasfilename(
            title="Salvar Excel", defaultextension=".xlsx",
            initialfile="prodtrack_completo.xlsx", filetypes=[("Planilha Excel", "*.xlsx")],
        )
        if not destino:
            return

        caminho = excel_service.exportar_atividades_para_excel(df, Path(destino))
        self.label_status_excel.configure(text=f"Exportado em: {caminho}")
        messagebox.showinfo("ProdTrack", f"Excel exportado com sucesso:\n{caminho}")

    def _importar_planilha(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar planilha Excel", filetypes=[("Planilhas Excel", "*.xlsx *.xls")],
        )
        if not caminho:
            return

        try:
            qtd, erros = excel_service.importar_atividades_de_excel(Path(caminho))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("ProdTrack", f"Erro ao ler o arquivo: {exc}")
            return

        mensagem = f"{qtd} atividade(s) importada(s)."
        if erros:
            mensagem += "\n\nAvisos:\n" + "\n".join(erros[:10])
        messagebox.showinfo("ProdTrack", mensagem)
        self.label_status_excel.configure(text=mensagem.splitlines()[0])

    # ------------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------------

    def _secao_backup(self, parent):
        ctk.CTkLabel(
            parent, text="BACKUP", font=theme.FONT_SECTION, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(theme.PAD_SECTION, 8))

        card = self._novo_card(parent)
        interno = ctk.CTkFrame(card, fg_color="transparent")
        interno.pack(fill="x", padx=20, pady=18)

        ctk.CTkLabel(
            interno, text="Um backup automático é criado a cada dia em que o app é aberto.",
            font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkButton(
            interno, text="Criar backup agora", command=self._criar_backup, **theme.estilo_botao_secundario(),
        ).pack(fill="x", pady=(0, 14))

        self.frame_lista_backups = ctk.CTkFrame(interno, fg_color="transparent")
        self.frame_lista_backups.pack(fill="x")

        self._atualizar_lista_backups()

    def _criar_backup(self):
        try:
            caminho = backup_service.criar_backup()
        except FileNotFoundError as exc:
            messagebox.showerror("ProdTrack", str(exc))
            return
        messagebox.showinfo("ProdTrack", f"Backup criado:\n{caminho}")
        self._atualizar_lista_backups()

    def _atualizar_lista_backups(self):
        for widget in self.frame_lista_backups.winfo_children():
            widget.destroy()

        backups = backup_service.listar_backups()
        if not backups:
            ctk.CTkLabel(
                self.frame_lista_backups, text="Nenhum backup encontrado ainda.",
                font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY,
            ).pack(anchor="w")
            return

        for item in backups[:10]:
            linha = ctk.CTkFrame(self.frame_lista_backups, fg_color="transparent")
            linha.pack(fill="x", pady=2)

            texto = f"{item['nome']} · {item['tamanho_kb']} KB · {item['criado_em']}"
            ctk.CTkLabel(
                linha, text=texto, font=theme.FONT_SMALL, text_color=theme.TEXT_PRIMARY, anchor="w",
            ).pack(side="left", fill="x", expand=True)

            botao_restaurar = ctk.CTkButton(
                linha, text="Restaurar", command=lambda c=item["caminho"]: self._restaurar_backup(c),
                fg_color="transparent", hover_color=theme.ROW_HOVER, text_color=theme.TEXT_PRIMARY,
                border_width=1, border_color=theme.BORDER, font=theme.FONT_SMALL,
                corner_radius=theme.RADIUS, width=90, height=28,
            )
            botao_restaurar.pack(side="right")

    def _restaurar_backup(self, caminho: str):
        confirmou = messagebox.askyesno(
            "Restaurar backup",
            "Restaurar este backup substituirá todos os dados atuais. Deseja continuar?",
        )
        if not confirmou:
            return

        backup_service.restaurar_backup(caminho)
        messagebox.showinfo("ProdTrack", "Backup restaurado. Reinicie o aplicativo para ver os dados atualizados.")
        self._atualizar_lista_backups()

    # ------------------------------------------------------------------
    # Util
    # ------------------------------------------------------------------

    def _novo_card(self, parent) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent, fg_color=theme.BG_CARD, border_width=1, border_color=theme.BORDER, corner_radius=theme.RADIUS
        )
        card.pack(fill="x")
        return card

    def atualizar(self):
        """Chamada ao entrar na tela."""
        pass
