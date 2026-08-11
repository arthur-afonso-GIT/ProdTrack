"""Ponte entre a interface Qt Quick/QML e as regras de negócio do ProdTrack."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtWidgets import QFileDialog

import models
from services import backup_service, excel_service, report_generator


MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def _parse_date(value: str) -> date:
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError("Data inválida. Use o formato dd/mm/aaaa.")


def _row_dict(row) -> dict:
    return {
        "id": int(row["id"]),
        "date": row["data"].strftime("%d/%m/%Y"),
        "name": str(row["nome_atividade"]),
        "minutes": int(row["tempo_minutos"]),
        "duration": models.minutos_para_horas_str(row["tempo_minutos"]),
        "evidence": str(row.get("evidencia") or ""),
        "notes": str(row.get("observacoes") or ""),
    }


class AppController(QObject):
    dataChanged = Signal()
    message = Signal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recent = []
        self._history = []
        self._backups = []
        self._fixed = []
        self._today = {}
        self._history_summary = ""
        self._refresh_all()

    def _refresh_all(self):
        summary = models.resumo_diario(date.today())
        target = summary["meta_horas"] * 60
        remaining = max(target - summary["total_minutos"], 0)
        self._today = {
            "total": summary["total_horas_str"],
            "target": f'{summary["meta_horas"]}h',
            "remaining": "Meta atingida" if remaining == 0 else models.minutos_para_horas_str(remaining),
            "progress": min(summary["total_minutos"] / target, 1.0) if target else 0,
        }
        df = models.listar_atividades()
        self._recent = [_row_dict(row) for _, row in df.head(8).iterrows()]
        self._backups = backup_service.listar_backups()[:10]
        self._fixed = [
            {
                "id": int(item["id"]),
                "name": item["nome_atividade"],
                "minutes": int(item["tempo_minutos"]),
                "duration": models.minutos_para_horas_str(item["tempo_minutos"]),
                "evidence": item["evidencia"] or "",
                "notes": item["observacoes"] or "",
            }
            for item in models.listar_atividades_fixas()
        ]
        self.dataChanged.emit()

    @Property("QVariantMap", notify=dataChanged)
    def today(self):
        return self._today

    @Property("QVariantList", notify=dataChanged)
    def recentActivities(self):
        return self._recent

    @Property("QVariantList", notify=dataChanged)
    def historyActivities(self):
        return self._history

    @Property(str, notify=dataChanged)
    def historySummary(self):
        return self._history_summary

    @Property("QVariantList", notify=dataChanged)
    def backups(self):
        return self._backups

    @Property("QVariantList", notify=dataChanged)
    def fixedActivities(self):
        return self._fixed

    @Property(int, notify=dataChanged)
    def workdayHours(self):
        return models.obter_jornada_diaria_horas()

    @Property(str, notify=dataChanged)
    def reportsDirectory(self):
        return models.obter_dir_relatorios()

    @Property(str, notify=dataChanged)
    def backupsDirectory(self):
        return models.obter_dir_backups()

    @Slot()
    def refresh(self):
        self._refresh_all()

    @Slot(str, result="QVariantList")
    def suggestions(self, text):
        return models.sugerir_atividades(text)

    @Slot(str, str, str, str, str, result=bool)
    def createActivity(self, day, name, minutes, evidence, notes):
        try:
            parsed_minutes = int(minutes)
            if parsed_minutes <= 0 or not name.strip():
                raise ValueError("Informe uma atividade e um tempo maior que zero.")
            models.criar_atividade(_parse_date(day), name, parsed_minutes, evidence, notes)
            self._refresh_all()
            self.message.emit("Atividade salva", "O registro foi adicionado com sucesso.", False)
            return True
        except (ValueError, TypeError) as exc:
            self.message.emit("Não foi possível salvar", str(exc), True)
            return False

    @Slot(result="QVariantMap")
    def repeatLast(self):
        item = models.buscar_ultima_atividade()
        if not item:
            self.message.emit("ProdTrack", "Ainda não há atividades registradas.", False)
            return {}
        return {"name": item["nome_atividade"], "minutes": str(item["tempo_minutos"]),
                "evidence": item["evidencia"] or "", "notes": item["observacoes"] or ""}

    @Slot(int, result="QVariantMap")
    def activity(self, activity_id):
        item = models.buscar_atividade_por_id(activity_id)
        if not item:
            return {}
        return {"id": item["id"], "date": datetime.strptime(item["data"], "%Y-%m-%d").strftime("%d/%m/%Y"),
                "name": item["nome_atividade"], "minutes": str(item["tempo_minutos"]),
                "evidence": item["evidencia"] or "", "notes": item["observacoes"] or ""}

    @Slot(int, str, str, str, str, str, result=bool)
    def updateActivity(self, activity_id, day, name, minutes, evidence, notes):
        try:
            value = int(minutes)
            if value <= 0 or not name.strip():
                raise ValueError("Informe uma atividade e um tempo maior que zero.")
            models.atualizar_atividade(activity_id, _parse_date(day), name, value, evidence, notes)
            self._refresh_all()
            return True
        except (ValueError, TypeError) as exc:
            self.message.emit("Não foi possível editar", str(exc), True)
            return False

    @Slot(int)
    def duplicateActivity(self, activity_id):
        models.duplicar_atividade(activity_id)
        self._refresh_all()

    @Slot(int)
    def deleteActivity(self, activity_id):
        models.excluir_atividade(activity_id)
        self._refresh_all()

    @Slot(str, str, str)
    def filterHistory(self, start, end, term):
        try:
            start_date = _parse_date(start) if start.strip() else None
            end_date = _parse_date(end) if end.strip() else None
            df = models.listar_atividades(start_date, end_date, term.strip() or None)
            self._history = [_row_dict(row) for _, row in df.iterrows()]
            total = models.minutos_para_horas_str(df["tempo_minutos"].sum()) if not df.empty else "0h 00min"
            self._history_summary = f"{len(df)} atividade(s) · total {total}"
            self.dataChanged.emit()
        except ValueError as exc:
            self.message.emit("Filtros inválidos", str(exc), True)

    @Slot(str, str, str, str)
    def filterHistoryPeriod(self, kind, year, option, term):
        try:
            year_value = int(year)
            option_value = int(option)
            if kind == "Mensal":
                start = date(year_value, option_value, 1)
                end = date(year_value + (option_value == 12), option_value % 12 + 1, 1) - timedelta(days=1)
            elif kind == "Trimestral":
                start, end = models.trimestre_para_periodo(year_value, option_value)
            elif kind == "Semestral":
                start, end = models.semestre_para_periodo(year_value, option_value)
            else:
                raise ValueError("Visão de histórico inválida.")
            df = models.listar_atividades(start, end, term.strip() or None)
            self._history = [_row_dict(row) for _, row in df.iterrows()]
            total = models.minutos_para_horas_str(df["tempo_minutos"].sum()) if not df.empty else "0h 00min"
            self._history_summary = (
                f"{kind} · {start:%d/%m/%Y} a {end:%d/%m/%Y} · "
                f"{len(df)} atividade(s) · total {total}"
            )
            self.dataChanged.emit()
        except (ValueError, TypeError) as exc:
            self.message.emit("Período inválido", str(exc), True)

    @Slot(str, str, str, str, result=bool)
    def createFixedActivity(self, name, minutes, evidence, notes):
        try:
            models.criar_atividade_fixa(name, int(minutes), evidence, notes)
            self._refresh_all()
            self.message.emit("Atividade fixa criada", "O modelo já está disponível no Dashboard.", False)
            return True
        except (ValueError, TypeError) as exc:
            self.message.emit("Não foi possível criar", str(exc), True)
            return False

    @Slot(int)
    def deleteFixedActivity(self, fixed_id):
        models.excluir_atividade_fixa(fixed_id)
        self._refresh_all()

    def _period(self, kind, day, year, option):
        if kind == "Diário":
            value = _parse_date(day)
            return value, value, f"Relatório Diário — {day}", 1
        year_value = int(year)
        if kind == "Mensal":
            month = int(option)
            start = date(year_value, month, 1)
            end = date(year_value + (month == 12), month % 12 + 1, 1) - timedelta(days=1)
            title = f"Relatório Mensal — {MESES[month - 1]}/{year_value}"
        elif kind == "Trimestral":
            start, end = models.trimestre_para_periodo(year_value, int(option))
            title = f"Relatório Trimestral — {option}º Trim/{year_value}"
        else:
            start, end = models.semestre_para_periodo(year_value, int(option))
            title = f"Relatório Semestral — {option}º Sem/{year_value}"
        days = sum(1 for n in range((end - start).days + 1) if (start + timedelta(days=n)).weekday() < 5)
        return start, end, title, days

    @Slot(str, str, str, str, result="QVariantMap")
    def reportSummary(self, kind, day, year, option):
        try:
            start, end, _, days = self._period(kind, day, year, option)
            df = models.listar_atividades(start, end)
            summary = models.resumo_periodo(df)
            hours = models.obter_jornada_diaria_horas()
            return {"hours": summary["total_horas_str"], "target": f"{hours * days}h",
                    "percent": f'{models.percentual_meta(summary["total_minutos"], hours, days)}%'}
        except (ValueError, TypeError) as exc:
            return {"error": str(exc)}

    @Slot(str, str, str, str)
    def generatePdf(self, kind, day, year, option):
        try:
            start, end, title, days = self._period(kind, day, year, option)
            path = report_generator.gerar_relatorio_pdf(
                models.listar_atividades(start, end), title, start, end,
                models.obter_jornada_diaria_horas(), days)
            self.message.emit("PDF gerado", str(path), False)
        except Exception as exc:  # UI boundary
            self.message.emit("Erro ao gerar PDF", str(exc), True)

    @Slot(str, str, str, str)
    def exportPeriod(self, kind, day, year, option):
        try:
            start, end, _, _ = self._period(kind, day, year, option)
            df = models.listar_atividades(start, end)
            if df.empty:
                raise ValueError("Nenhuma atividade no período selecionado.")
            suggested = f"prodtrack_{start:%Y%m%d}_{end:%Y%m%d}.xlsx"
            path, _ = QFileDialog.getSaveFileName(None, "Salvar Excel", suggested, "Planilha Excel (*.xlsx)")
            if path:
                result = excel_service.exportar_atividades_para_excel(df, Path(path))
                self.message.emit("Excel exportado", str(result), False)
        except Exception as exc:
            self.message.emit("Erro ao exportar", str(exc), True)

    @Slot(result=str)
    def chooseEvidence(self):
        path, _ = QFileDialog.getOpenFileName(None, "Selecionar arquivo de evidência")
        return path

    @Slot(int)
    def setWorkday(self, hours):
        models.definir_jornada_diaria_horas(hours)
        self._refresh_all()

    @Slot(str, result=str)
    def chooseDirectory(self, kind):
        path = QFileDialog.getExistingDirectory(None, "Escolher diretório")
        if path:
            (models.definir_dir_relatorios if kind == "reports" else models.definir_dir_backups)(path)
            self._refresh_all()
        return path

    @Slot()
    def exportAll(self):
        df = models.listar_atividades()
        if df.empty:
            self.message.emit("ProdTrack", "Não há atividades para exportar.", False)
            return
        path, _ = QFileDialog.getSaveFileName(None, "Salvar Excel", "prodtrack_completo.xlsx", "Planilha Excel (*.xlsx)")
        if path:
            result = excel_service.exportar_atividades_para_excel(df, Path(path))
            self.message.emit("Excel exportado", str(result), False)

    @Slot()
    def importSpreadsheet(self):
        path, _ = QFileDialog.getOpenFileName(None, "Selecionar planilha", "", "Planilhas Excel (*.xlsx *.xls)")
        if path:
            try:
                count, errors = excel_service.importar_atividades_de_excel(Path(path))
                detail = f"{count} atividade(s) importada(s)."
                if errors:
                    detail += "\n\n" + "\n".join(errors[:10])
                self._refresh_all()
                self.message.emit("Importação concluída", detail, bool(errors))
            except Exception as exc:
                self.message.emit("Erro ao importar", str(exc), True)

    @Slot()
    def createBackup(self):
        try:
            path = backup_service.criar_backup()
            self._refresh_all()
            self.message.emit("Backup criado", str(path), False)
        except Exception as exc:
            self.message.emit("Erro ao criar backup", str(exc), True)

    @Slot(str)
    def restoreBackup(self, path):
        try:
            backup_service.restaurar_backup(path)
            self._refresh_all()
            self.message.emit("Backup restaurado", "Os dados foram restaurados com sucesso.", False)
        except Exception as exc:
            self.message.emit("Erro ao restaurar", str(exc), True)
