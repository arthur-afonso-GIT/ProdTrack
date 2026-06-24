"""
ui/main_window.py
Janela principal do ProdTrack: barra de navegação superior simples
([Início] [Histórico] [Relatórios] [Configurações]) e área de conteúdo
que troca entre as telas (frames). Sem sidebar — navegação enxuta no topo.
"""

import customtkinter as ctk

from ui import theme
from ui.dashboard_frame import DashboardFrame
from ui.history_frame import HistoryFrame
from ui.reports_frame import ReportsFrame
from ui.settings_frame import SettingsFrame


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ProdTrack")
        self.geometry("900x720")
        self.minsize(720, 560)
        self.configure(fg_color=theme.BG)

        self._frames: dict[str, ctk.CTkFrame] = {}
        self._botoes_nav: dict[str, ctk.CTkButton] = {}
        self._pagina_atual = None

        self._construir_navegacao()
        self._construir_area_conteudo()
        self._criar_paginas()
        self.mostrar_pagina("Início")

    # ------------------------------------------------------------------
    # Navegação superior
    # ------------------------------------------------------------------

    def _construir_navegacao(self):
        barra = ctk.CTkFrame(self, fg_color=theme.NAV_BG, corner_radius=0, height=56)
        barra.pack(fill="x", side="top")

        # Linha fina de separação entre a navegação e o conteúdo
        separador = ctk.CTkFrame(self, fg_color=theme.BORDER, height=1, corner_radius=0)
        separador.pack(fill="x", side="top")

        interno = ctk.CTkFrame(barra, fg_color="transparent")
        interno.pack(fill="both", expand=True, padx=theme.PAD_PAGE)

        marca = ctk.CTkLabel(interno, text="✅ ProdTrack", font=theme.FONT_BRAND, text_color=theme.TEXT_PRIMARY)
        marca.pack(side="left", pady=12)

        nav_itens = ctk.CTkFrame(interno, fg_color="transparent")
        nav_itens.pack(side="left", padx=(32, 0))

        self._nav_itens_frame = nav_itens

    def _criar_botao_nav(self, nome: str, icone_texto: str):
        botao = ctk.CTkButton(
            self._nav_itens_frame,
            text=f"{icone_texto}  {nome}",
            command=lambda: self.mostrar_pagina(nome),
            fg_color="transparent",
            hover_color=theme.ROW_HOVER,
            text_color=theme.TEXT_SECONDARY,
            font=theme.FONT_NAV_ITEM,
            corner_radius=theme.RADIUS,
            height=36,
        )
        botao.pack(side="left", padx=4, pady=12)
        self._botoes_nav[nome] = botao

    # ------------------------------------------------------------------
    # Área de conteúdo (onde os frames são mostrados)
    # ------------------------------------------------------------------

    def _construir_area_conteudo(self):
        self._area_conteudo = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0)
        self._area_conteudo.pack(fill="both", expand=True)

    def _criar_paginas(self):
        paginas = [
            ("Início", "🏠", DashboardFrame),
            ("Histórico", "📋", HistoryFrame),
            ("Relatórios", "📄", ReportsFrame),
            ("Configurações", "⚙️", SettingsFrame),
        ]

        for nome, icone, classe_frame in paginas:
            self._criar_botao_nav(nome, icone)
            frame = classe_frame(self._area_conteudo)
            frame.place(in_=self._area_conteudo, x=0, y=0, relwidth=1, relheight=1)
            self._frames[nome] = frame

    def mostrar_pagina(self, nome: str):
        frame = self._frames.get(nome)
        if frame is None:
            return

        frame.lift()
        if hasattr(frame, "atualizar"):
            frame.atualizar()

        for nome_botao, botao in self._botoes_nav.items():
            if nome_botao == nome:
                botao.configure(fg_color=theme.ROW_HOVER, text_color=theme.ACCENT)
            else:
                botao.configure(fg_color="transparent", text_color=theme.TEXT_SECONDARY)

        self._pagina_atual = nome
