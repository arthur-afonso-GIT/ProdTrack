"""
main.py
Ponto de entrada do ProdTrack — aplicação desktop de registro rápido
de atividades de teletrabalho.

Execução:
    python main.py
"""

import customtkinter as ctk

from database import init_db
from services import backup_service
from ui import theme
from ui.main_window import MainWindow


def main():
    init_db()

    # Backup automático: roda uma vez por dia, na primeira execução do dia
    if backup_service.deve_fazer_backup_diario():
        try:
            backup_service.criar_backup()
        except FileNotFoundError:
            pass  # banco recém-criado, ainda sem dados — ignora

    theme.aplicar_tema_global()

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
