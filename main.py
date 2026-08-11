"""
main.py
Ponto de entrada do ProdTrack — aplicação desktop de registro rápido
de atividades de teletrabalho.

Execução:
    python main.py
"""

import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from database import init_db
from services import backup_service
from ui.app_controller import AppController


def main():
    init_db()

    # Backup automático: roda uma vez por dia, na primeira execução do dia
    if backup_service.deve_fazer_backup_diario():
        try:
            backup_service.criar_backup()
        except FileNotFoundError:
            pass  # banco recém-criado, ainda sem dados — ignora

    app = QApplication(sys.argv)
    app.setApplicationName("ProdTrack")
    app.setOrganizationName("ProdTrack")

    engine = QQmlApplicationEngine()
    controller = AppController(engine)
    engine.rootContext().setContextProperty("appController", controller)
    qml_file = Path(__file__).resolve().parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    if not engine.rootObjects():
        return 1
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
