"""
ui/autocomplete_entry.py
Campo de texto com sugestões em dropdown (autocomplete), usado no
campo "Atividade" do formulário de registro.

CustomTkinter não tem um combobox com autocomplete nativo, então
implementamos manualmente: um CTkEntry normal + uma pequena lista de
sugestões (CTkFrame com botões) que aparece flutuando logo abaixo do
campo enquanto o usuário digita, e desaparece ao escolher uma opção,
perder o foco, ou apertar Esc.
"""

from typing import Callable

import customtkinter as ctk

from ui import theme


class AutocompleteEntry(ctk.CTkFrame):
    """
    Um CTkEntry com uma lista de sugestões que aparece abaixo dele.

    fornecedor_sugestoes: função que recebe o texto digitado (str) e
        retorna uma lista de strings sugeridas (já filtrada e ordenada).
    on_change: callback opcional chamado a cada tecla digitada, recebendo
        o texto atual do campo.
    """

    def __init__(
        self,
        master,
        fornecedor_sugestoes: Callable[[str], list[str]],
        placeholder_text: str = "",
        on_change: Callable[[str], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent")

        self._fornecedor_sugestoes = fornecedor_sugestoes
        self._on_change = on_change
        self._botoes_sugestao: list[ctk.CTkButton] = []

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder_text,
            **theme.estilo_entry(),
            **kwargs,
        )
        self.entry.pack(fill="x")
        self.entry.bind("<KeyRelease>", self._ao_digitar)
        self.entry.bind("<FocusOut>", self._ao_perder_foco)
        self.entry.bind("<Escape>", lambda e: self._esconder_sugestoes())
        self.entry.bind("<Down>", self._focar_primeira_sugestao)

        # Container das sugestões — só é "packado" quando há algo a mostrar
        self.frame_sugestoes = ctk.CTkFrame(
            self,
            fg_color=theme.BG_CARD,
            border_width=1,
            border_color=theme.BORDER,
            corner_radius=theme.RADIUS,
        )

    # ------------------------------------------------------------------
    # API pública — mesma interface básica de um CTkEntry
    # ------------------------------------------------------------------

    def get(self) -> str:
        return self.entry.get()

    def set(self, valor: str) -> None:
        self.entry.delete(0, "end")
        self.entry.insert(0, valor)

    def focus(self) -> None:
        self.entry.focus()

    # ------------------------------------------------------------------
    # Lógica interna do autocomplete
    # ------------------------------------------------------------------

    def _ao_digitar(self, event=None):
        # Teclas de navegação não devem re-disparar a busca de sugestões
        if event is not None and event.keysym in ("Down", "Up", "Return", "Escape"):
            return

        texto_atual = self.entry.get()

        if self._on_change:
            self._on_change(texto_atual)

        sugestoes = self._fornecedor_sugestoes(texto_atual) if texto_atual.strip() else []

        if sugestoes:
            self._mostrar_sugestoes(sugestoes)
        else:
            self._esconder_sugestoes()

    def _mostrar_sugestoes(self, sugestoes: list[str]):
        # Limpa botões antigos antes de recriar
        for botao in self._botoes_sugestao:
            botao.destroy()
        self._botoes_sugestao.clear()

        for nome in sugestoes:
            botao = ctk.CTkButton(
                self.frame_sugestoes,
                text=nome,
                anchor="w",
                fg_color="transparent",
                hover_color=theme.ROW_HOVER,
                text_color=theme.TEXT_PRIMARY,
                font=theme.FONT_BODY,
                corner_radius=0,
                height=30,
                command=lambda n=nome: self._selecionar_sugestao(n),
            )
            botao.pack(fill="x", padx=2, pady=1)
            self._botoes_sugestao.append(botao)

        self.frame_sugestoes.pack(fill="x", pady=(2, 0))

    def _esconder_sugestoes(self):
        self.frame_sugestoes.pack_forget()

    def _selecionar_sugestao(self, nome: str):
        self.set(nome)
        self._esconder_sugestoes()
        if self._on_change:
            self._on_change(nome)
        self.entry.focus()

    def _ao_perder_foco(self, event=None):
        # Pequeno delay: se o foco foi para um botão de sugestão (clique),
        # não escondemos antes do clique ser processado.
        self.after(150, self._esconder_sugestoes)

    def _focar_primeira_sugestao(self, event=None):
        if self._botoes_sugestao:
            self._botoes_sugestao[0].focus()
            return "break"
