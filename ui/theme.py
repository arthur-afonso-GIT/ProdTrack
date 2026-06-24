"""
ui/theme.py
Sistema de design do ProdTrack — cores, tipografia e espaçamentos
centralizados, para que todas as telas tenham aparência consistente.

Paleta inspirada em ferramentas pessoais de produtividade (Notion,
Todoist, TickTick, Linear): fundo claro e neutro, um único accent
vivo para a ação principal, tipografia limpa, zero gradientes.
"""

import customtkinter as ctk

# --------------------------------------------------------------------------
# Paleta de cores
# --------------------------------------------------------------------------

BG = "#FAFAF8"            # fundo geral da janela
BG_CARD = "#FFFFFF"       # fundo de cartões/inputs
BORDER = "#E8E6E0"        # bordas sutis
TEXT_PRIMARY = "#1A1A1A"  # texto principal
TEXT_SECONDARY = "#8A8A8A"  # texto secundário / labels / metadados
ACCENT = "#5B5FEF"        # accent único — ação primária (violeta-azulado)
ACCENT_HOVER = "#4A4DD9"  # accent em hover
SUCCESS = "#3DA35D"       # usado só para "meta atingida"
DANGER = "#D64545"        # usado só para exclusão/erros
DANGER_HOVER = "#B83A3A"
ROW_HOVER = "#F1F0EC"     # hover em linhas de lista / itens de navegação
NAV_BG = "#FFFFFF"        # fundo da barra de navegação superior

# --------------------------------------------------------------------------
# Tipografia
# --------------------------------------------------------------------------
# CustomTkinter aceita tuplas (família, tamanho, peso) como "font".
# Usamos uma família comum a Windows/macOS/Linux para evitar problemas
# de fonte ausente em diferentes sistemas operacionais.

FONT_FAMILY = "Segoe UI"  # fallback automático para system font em outros SOs

FONT_BRAND = (FONT_FAMILY, 18, "bold")
FONT_H1 = (FONT_FAMILY, 15, "bold")
FONT_SECTION = (FONT_FAMILY, 11, "bold")        # cabeçalhos de seção (uppercase)
FONT_BODY = (FONT_FAMILY, 13, "normal")
FONT_BODY_BOLD = (FONT_FAMILY, 13, "bold")
FONT_SMALL = (FONT_FAMILY, 11, "normal")
FONT_BIG_NUMBER = (FONT_FAMILY, 22, "bold")     # "Hoje: 4h20m" etc.
FONT_NAV_ITEM = (FONT_FAMILY, 13, "bold")
FONT_BUTTON = (FONT_FAMILY, 13, "bold")

# --------------------------------------------------------------------------
# Espaçamentos padrão
# --------------------------------------------------------------------------

PAD_PAGE = 24       # respiro nas bordas de cada tela
PAD_SECTION = 18    # espaço entre seções dentro de uma tela
PAD_FIELD = 8       # espaço entre campos de um formulário
RADIUS = 8          # corner_radius padrão de botões/inputs/cartões


def aplicar_tema_global():
    """Configura o modo de aparência e tema de cor base do CustomTkinter."""
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")  # base neutra; sobrescrevemos cores manualmente


def estilo_botao_primario() -> dict:
    """Kwargs padrão para o botão de ação principal (ex.: 'Salvar atividade')."""
    return {
        "fg_color": ACCENT,
        "hover_color": ACCENT_HOVER,
        "text_color": "#FFFFFF",
        "font": FONT_BUTTON,
        "corner_radius": RADIUS,
        "height": 42,
    }


def estilo_botao_secundario() -> dict:
    """Kwargs padrão para botões secundários (ex.: 'Cancelar', 'Repetir última')."""
    return {
        "fg_color": "transparent",
        "hover_color": ROW_HOVER,
        "text_color": TEXT_PRIMARY,
        "border_width": 1,
        "border_color": BORDER,
        "font": FONT_BODY,
        "corner_radius": RADIUS,
        "height": 36,
    }


def estilo_botao_perigo() -> dict:
    """Kwargs padrão para botões destrutivos (ex.: 'Excluir', 'Sim, excluir')."""
    return {
        "fg_color": "transparent",
        "hover_color": "#FBEAEA",
        "text_color": DANGER,
        "border_width": 1,
        "border_color": "#F0D0D0",
        "font": FONT_BODY,
        "corner_radius": RADIUS,
        "height": 32,
    }


def estilo_botao_icone() -> dict:
    """Kwargs para botões pequenos só com ícone (editar/duplicar/excluir em linhas de lista)."""
    return {
        "fg_color": "transparent",
        "hover_color": ROW_HOVER,
        "text_color": TEXT_SECONDARY,
        "font": FONT_BODY,
        "corner_radius": RADIUS,
        "width": 32,
        "height": 28,
    }


def estilo_entry() -> dict:
    """Kwargs padrão para campos de texto/data/número."""
    return {
        "fg_color": BG_CARD,
        "border_color": BORDER,
        "border_width": 1,
        "text_color": TEXT_PRIMARY,
        "font": FONT_BODY,
        "corner_radius": RADIUS,
        "height": 38,
    }
