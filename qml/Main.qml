import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Material

ApplicationWindow {
    id: window
    width: 1100
    height: 760
    minimumWidth: 820
    minimumHeight: 620
    visible: true
    title: "ProdTrack"
    color: "#f6f7fb"
    Material.theme: Material.Light
    Material.accent: "#4f46e5"
    property int page: 0
    property string todayText: Qt.formatDate(new Date(), "dd/MM/yyyy")

    component SectionTitle: Label {
        font.pixelSize: 12
        font.bold: true
        font.letterSpacing: 1.2
        color: "#667085"
    }
    component Card: Rectangle {
        color: "white"
        radius: 12
        border.color: "#e4e7ec"
        border.width: 1
    }
    component Metric: ColumnLayout {
        property alias label: metricLabel.text
        property alias value: metricValue.text
        spacing: 2
        Label { id: metricLabel; color: "#667085"; font.pixelSize: 12 }
        Label { id: metricValue; color: "#101828"; font.pixelSize: 24; font.bold: true }
    }

    header: Rectangle {
        height: 68
        color: "white"
        border.color: "#e4e7ec"
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 28
            anchors.rightMargin: 28
            Label { text: "ProdTrack"; font.pixelSize: 22; font.bold: true; color: "#101828"; Layout.rightMargin: 30 }
            Repeater {
                model: ["Início", "Histórico", "Relatórios", "Configurações"]
                delegate: Button {
                    required property int index
                    required property string modelData
                    text: modelData
                    flat: true
                    highlighted: window.page === index
                    onClicked: {
                        window.page = index
                        if (index === 1) historyPage.applyFilter()
                        else appController.refresh()
                    }
                }
            }
            Item { Layout.fillWidth: true }
        }
    }

    StackLayout {
        anchors.fill: parent
        currentIndex: window.page

        // Dashboard
        ScrollView {
            contentWidth: availableWidth
            ColumnLayout {
                width: parent.width - 60
                x: 30
                y: 26
                spacing: 18
                RowLayout {
                    Layout.fillWidth: true; spacing: 48
                    Metric { label: "Hoje"; value: appController.today.total || "0h 00min" }
                    Metric { label: "Meta"; value: appController.today.target || "8h" }
                    Metric { label: "Faltam"; value: appController.today.remaining || "8h 00min" }
                    Item { Layout.fillWidth: true }
                }
                ProgressBar { Layout.fillWidth: true; value: appController.today.progress || 0 }
                SectionTitle { visible: appController.fixedActivities.length > 0; text: "ATIVIDADES FIXAS" }
                Flow {
                    visible: appController.fixedActivities.length > 0
                    Layout.fillWidth: true
                    spacing: 8
                    Repeater {
                        model: appController.fixedActivities
                        delegate: Button {
                            required property var modelData
                            text: modelData.name + " · " + modelData.duration
                            onClicked: {
                                inputActivity.text = modelData.name
                                inputHours.text = String(Math.floor(modelData.minutes / 60))
                                inputMinutes.text = String(modelData.minutes % 60)
                                inputStart.clear()
                                inputEnd.clear()
                                inputEvidence.text = modelData.evidence
                                inputNotes.text = modelData.notes
                            }
                        }
                    }
                }
                SectionTitle { text: "REGISTRAR ATIVIDADE" }
                Card {
                    Layout.fillWidth: true; implicitHeight: form.implicitHeight + 36
                    ColumnLayout {
                        id: form
                        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 18 }
                        spacing: 10
                        RowLayout {
                            Layout.fillWidth: true
                            ColumnLayout {
                                Layout.fillWidth: true
                                Label { text: "Data" }
                                TextField { id: inputDay; text: window.todayText; Layout.fillWidth: true }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Label { text: "Atividade" }
                                RowLayout {
                                    Layout.fillWidth: true
                                    TextField { id: inputActivity; Layout.fillWidth: true; placeholderText: "O que você fez?" }
                                    Button {
                                        text: "Repetir última"
                                        flat: true
                                        Layout.alignment: Qt.AlignVCenter
                                        onClicked: {
                                            const item = appController.repeatLast()
                                            if (item.name) {
                                                inputActivity.text = item.name; inputHours.text = item.hours
                                                inputMinutes.text = item.minutes; inputStart.text = item.start
                                                inputEnd.text = item.end; inputEvidence.text = item.evidence
                                                inputNotes.text = item.notes
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            ColumnLayout {
                                Layout.fillWidth: true
                                Label { text: "Duração" }
                                RowLayout {
                                    Layout.fillWidth: true
                                    TextField { id: inputHours; text: "0"; placeholderText: "Horas"; Layout.fillWidth: true; inputMethodHints: Qt.ImhDigitsOnly }
                                    Label { text: "h" }
                                    TextField { id: inputMinutes; text: "30"; placeholderText: "Minutos"; Layout.fillWidth: true; inputMethodHints: Qt.ImhDigitsOnly }
                                    Label { text: "min" }
                                }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Label { text: "Horário (opcional — calcula a duração)" }
                                RowLayout {
                                    Layout.fillWidth: true
                                    TextField { id: inputStart; placeholderText: "Início  HH:MM"; Layout.fillWidth: true; maximumLength: 5 }
                                    Label { text: "até" }
                                    TextField { id: inputEnd; placeholderText: "Término  HH:MM"; Layout.fillWidth: true; maximumLength: 5 }
                                }
                            }
                        }
                        Label { text: "Evidência" }
                        RowLayout {
                            Layout.fillWidth: true
                            TextField { id: inputEvidence; Layout.fillWidth: true; placeholderText: "Link ou caminho do arquivo" }
                            Button { text: "Anexar"; onClicked: { const path = appController.chooseEvidence(); if (path) inputEvidence.text = path } }
                        }
                        Label { text: "Observações" }
                        TextArea { id: inputNotes; Layout.fillWidth: true; Layout.preferredHeight: 65; wrapMode: TextEdit.Wrap }
                        Button {
                            text: "Salvar atividade"; highlighted: true; Layout.fillWidth: true
                            onClicked: if (appController.createActivity(inputDay.text, inputActivity.text,
                                                                        inputHours.text, inputMinutes.text,
                                                                        inputStart.text, inputEnd.text,
                                                                        inputEvidence.text, inputNotes.text)) {
                                inputDay.text = window.todayText; inputActivity.clear(); inputHours.text = "0"
                                inputMinutes.text = "30"; inputStart.clear(); inputEnd.clear()
                                inputEvidence.clear(); inputNotes.clear(); inputActivity.forceActiveFocus()
                            }
                        }
                    }
                }
                SectionTitle { text: "ATIVIDADES RECENTES" }
                Label { visible: appController.recentActivities.length === 0; text: "Nenhuma atividade registrada ainda."; color: "#667085" }
                Repeater {
                    model: appController.recentActivities
                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true; height: 66; color: "transparent"
                        border.color: "#e4e7ec"; border.width: 0
                        RowLayout {
                            anchors.fill: parent
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 2
                                Label { text: modelData.name; font.bold: true; color: "#101828" }
                                Label {
                                    text: modelData.date + " · " + modelData.duration
                                          + (modelData.schedule ? " · " + modelData.schedule : "")
                                          + (modelData.evidence ? " · " + modelData.evidence : "")
                                    color: "#667085"; elide: Text.ElideRight; Layout.fillWidth: true
                                }
                            }
                            Button { text: "Editar"; flat: true; onClicked: editDialog.openActivity(modelData.id) }
                            Button { text: "Duplicar"; flat: true; onClicked: appController.duplicateActivity(modelData.id) }
                            Button { text: "Excluir"; flat: true; onClicked: confirmDelete.ask(modelData.id, modelData.name) }
                        }
                    }
                }
            }
        }

        // Histórico
        ColumnLayout {
            id: historyPage
            Layout.fillWidth: true; Layout.fillHeight: true
            Layout.leftMargin: 30; Layout.rightMargin: 30; Layout.topMargin: 26; Layout.bottomMargin: 24
            spacing: 14
            function applyFilter() {
                if (historyView.currentText === "Personalizado")
                    appController.filterHistory(historyStart.text, historyEnd.text, historyTerm.text)
                else
                    appController.filterHistoryPeriod(historyView.currentText, historyYear.text,
                                                      String(historyOption.currentValue), historyTerm.text)
            }
            SectionTitle { text: "HISTÓRICO" }
            RowLayout {
                Layout.fillWidth: true
                ComboBox {
                    id: historyView
                    model: ["Personalizado", "Mensal", "Trimestral", "Semestral"]
                    currentIndex: 1
                    Layout.preferredWidth: 150
                    onCurrentTextChanged: {
                        if (currentText === "Mensal") historyOption.currentIndex = new Date().getMonth()
                        else if (currentText === "Trimestral") historyOption.currentIndex = Math.floor(new Date().getMonth() / 3)
                        else if (currentText === "Semestral") historyOption.currentIndex = Math.floor(new Date().getMonth() / 6)
                    }
                }
                TextField { id: historyStart; visible: historyView.currentText === "Personalizado"; text: Qt.formatDate(new Date(new Date().getTime() - 30*86400000), "dd/MM/yyyy"); placeholderText: "De"; Layout.fillWidth: true }
                TextField { id: historyEnd; visible: historyView.currentText === "Personalizado"; text: window.todayText; placeholderText: "Até"; Layout.fillWidth: true }
                TextField { id: historyYear; visible: historyView.currentText !== "Personalizado"; text: String(new Date().getFullYear()); placeholderText: "Ano"; Layout.preferredWidth: 110 }
                ComboBox {
                    id: historyOption
                    visible: historyView.currentText !== "Personalizado"
                    Layout.fillWidth: true
                    textRole: "text"; valueRole: "value"
                    model: historyView.currentText === "Mensal" ? [
                        {text:"Janeiro",value:1},{text:"Fevereiro",value:2},{text:"Março",value:3},{text:"Abril",value:4},{text:"Maio",value:5},{text:"Junho",value:6},
                        {text:"Julho",value:7},{text:"Agosto",value:8},{text:"Setembro",value:9},{text:"Outubro",value:10},{text:"Novembro",value:11},{text:"Dezembro",value:12}
                    ] : historyView.currentText === "Trimestral" ? [{text:"1º trimestre",value:1},{text:"2º trimestre",value:2},{text:"3º trimestre",value:3},{text:"4º trimestre",value:4}]
                      : [{text:"1º semestre",value:1},{text:"2º semestre",value:2}]
                }
                TextField { id: historyTerm; placeholderText: "Buscar atividade"; Layout.fillWidth: true; onAccepted: historyPage.applyFilter() }
                Button { text: "Filtrar"; highlighted: true; onClicked: historyPage.applyFilter() }
            }
            Label { text: appController.historySummary; color: "#667085" }
            Rectangle {
                Layout.fillWidth: true; height: 36; color: "#eef2ff"; radius: 6
                RowLayout { anchors.fill: parent; anchors.leftMargin: 10; anchors.rightMargin: 10
                    Label { text: "Data"; font.bold: true; Layout.preferredWidth: 100 }
                    Label { text: "Atividade"; font.bold: true; Layout.fillWidth: true }
                    Label { text: "Tempo"; font.bold: true; Layout.preferredWidth: 100 }
                    Label { text: "Horário"; font.bold: true; Layout.preferredWidth: 110 }
                    Label { text: "Ações"; font.bold: true; Layout.preferredWidth: 190 }
                }
            }
            ListView {
                Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 1
                model: appController.historyActivities
                delegate: Rectangle {
                    required property var modelData
                    width: ListView.view.width; height: 54; color: index % 2 ? "#fafafa" : "white"
                    RowLayout { anchors.fill: parent; anchors.leftMargin: 10; anchors.rightMargin: 10
                        Label { text: modelData.date; Layout.preferredWidth: 100 }
                        Label { text: modelData.name; Layout.fillWidth: true; elide: Text.ElideRight }
                        Label { text: modelData.duration; Layout.preferredWidth: 100 }
                        Label { text: modelData.schedule || "—"; Layout.preferredWidth: 110; color: "#667085" }
                        RowLayout { Layout.preferredWidth: 190
                            Button { text: "Editar"; flat: true; onClicked: editDialog.openActivity(modelData.id) }
                            Button { text: "Duplicar"; flat: true; onClicked: { appController.duplicateActivity(modelData.id); historyPage.applyFilter() } }
                            Button { text: "Excluir"; flat: true; onClicked: confirmDelete.ask(modelData.id, modelData.name) }
                        }
                    }
                }
            }
        }

        // Relatórios
        ColumnLayout {
            id: reportsPage
            Layout.fillWidth: true; Layout.fillHeight: true
            Layout.leftMargin: 30; Layout.rightMargin: 30; Layout.topMargin: 26; Layout.bottomMargin: 30
            spacing: 18
            property var summary: ({"hours":"0h 00min", "target":"0h", "percent":"0%"})
            function refreshSummary() { summary = appController.reportSummary(reportKind.currentText, reportDay.text, reportYear.text, String(reportOption.currentValue)) }
            SectionTitle { text: "RELATÓRIOS" }
            ComboBox { id: reportKind; Layout.fillWidth: true; model: ["Diário", "Mensal", "Trimestral", "Semestral"]; onCurrentTextChanged: { reportOption.currentIndex = 0; reportsPage.refreshSummary() } }
            Card {
                Layout.fillWidth: true; height: 112
                RowLayout {
                    anchors.fill: parent; anchors.margins: 20
                    TextField { id: reportDay; visible: reportKind.currentText === "Diário"; text: window.todayText; placeholderText: "Dia"; Layout.fillWidth: true; onEditingFinished: reportsPage.refreshSummary() }
                    TextField { id: reportYear; visible: reportKind.currentText !== "Diário"; text: String(new Date().getFullYear()); placeholderText: "Ano"; Layout.fillWidth: true; onEditingFinished: reportsPage.refreshSummary() }
                    ComboBox {
                        id: reportOption; visible: reportKind.currentText !== "Diário"; Layout.fillWidth: true
                        textRole: "text"; valueRole: "value"
                        model: reportKind.currentText === "Mensal" ? [
                            {text:"Janeiro",value:1},{text:"Fevereiro",value:2},{text:"Março",value:3},{text:"Abril",value:4},{text:"Maio",value:5},{text:"Junho",value:6},
                            {text:"Julho",value:7},{text:"Agosto",value:8},{text:"Setembro",value:9},{text:"Outubro",value:10},{text:"Novembro",value:11},{text:"Dezembro",value:12}
                        ] : reportKind.currentText === "Trimestral" ? [{text:"1º trimestre",value:1},{text:"2º trimestre",value:2},{text:"3º trimestre",value:3},{text:"4º trimestre",value:4}]
                          : [{text:"1º semestre",value:1},{text:"2º semestre",value:2}]
                        onCurrentValueChanged: reportsPage.refreshSummary()
                    }
                }
            }
            RowLayout { spacing: 48
                Metric { label: "Horas registradas"; value: reportsPage.summary.hours || "—" }
                Metric { label: "Meta do período"; value: reportsPage.summary.target || "—" }
                Metric { label: "% atingido"; value: reportsPage.summary.percent || "—" }
            }
            RowLayout {
                Layout.fillWidth: true
                Button { text: "Gerar PDF"; highlighted: true; Layout.fillWidth: true; onClicked: appController.generatePdf(reportKind.currentText, reportDay.text, reportYear.text, String(reportOption.currentValue)) }
                Button { text: "Exportar Excel"; Layout.fillWidth: true; onClicked: appController.exportPeriod(reportKind.currentText, reportDay.text, reportYear.text, String(reportOption.currentValue)) }
            }
            Item { Layout.fillHeight: true }
        }

        // Configurações
        ScrollView {
            contentWidth: availableWidth
            ColumnLayout {
                width: parent.width - 60; x: 30; y: 26; spacing: 16
                SectionTitle { text: "JORNADA DIÁRIA" }
                Card {
                    Layout.fillWidth: true; height: 78
                    RowLayout { anchors.centerIn: parent
                        Repeater { model: [6, 7, 8]; Button { required property int modelData; text: modelData + "h/dia"; highlighted: appController.workdayHours === modelData; onClicked: appController.setWorkday(modelData) } }
                    }
                }
                SectionTitle { text: "ATIVIDADES FIXAS" }
                Card {
                    Layout.fillWidth: true; implicitHeight: fixedForm.implicitHeight + 36
                    ColumnLayout {
                        id: fixedForm
                        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 18 }
                        RowLayout {
                            Layout.fillWidth: true
                            TextField { id: fixedName; placeholderText: "Nome da atividade"; Layout.fillWidth: true }
                            TextField { id: fixedHours; placeholderText: "Horas"; inputMethodHints: Qt.ImhDigitsOnly; Layout.preferredWidth: 90 }
                            Label { text: "h" }
                            TextField { id: fixedMinutes; placeholderText: "Minutos"; inputMethodHints: Qt.ImhDigitsOnly; Layout.preferredWidth: 100 }
                            Label { text: "min" }
                            Button {
                                text: "Criar atividade fixa"; highlighted: true
                                onClicked: if (appController.createFixedActivity(fixedName.text, fixedHours.text,
                                                                                fixedMinutes.text, fixedEvidence.text,
                                                                                fixedNotes.text)) {
                                    fixedName.clear(); fixedHours.clear(); fixedMinutes.clear(); fixedEvidence.clear(); fixedNotes.clear()
                                }
                            }
                        }
                        TextField { id: fixedEvidence; placeholderText: "Evidência padrão (opcional)"; Layout.fillWidth: true }
                        TextArea { id: fixedNotes; placeholderText: "Observações padrão (opcional)"; Layout.fillWidth: true; Layout.preferredHeight: 58 }
                        Repeater {
                            model: appController.fixedActivities
                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Label { text: modelData.name + " · " + modelData.duration; Layout.fillWidth: true }
                                Button { text: "Remover"; flat: true; onClicked: appController.deleteFixedActivity(modelData.id) }
                            }
                        }
                        Label { visible: appController.fixedActivities.length === 0; text: "Nenhuma atividade fixa criada."; color: "#667085" }
                    }
                }
                SectionTitle { text: "DIRETÓRIOS PADRÃO" }
                Card {
                    Layout.fillWidth: true; height: 142
                    ColumnLayout { anchors.fill: parent; anchors.margins: 18
                        RowLayout {
                            Layout.fillWidth: true
                            TextField { text: appController.reportsDirectory; readOnly: true; Layout.fillWidth: true }
                            Button { text: "Relatórios…"; onClicked: appController.chooseDirectory("reports") }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            TextField { text: appController.backupsDirectory; readOnly: true; Layout.fillWidth: true }
                            Button { text: "Backups…"; onClicked: appController.chooseDirectory("backups") }
                        }
                    }
                }
                SectionTitle { text: "IMPORTAR / EXPORTAR EXCEL" }
                RowLayout {
                    Layout.fillWidth: true
                    Button { text: "Exportar tudo"; Layout.fillWidth: true; onClicked: appController.exportAll() }
                    Button { text: "Importar planilha"; Layout.fillWidth: true; onClicked: appController.importSpreadsheet() }
                }
                SectionTitle { text: "BACKUP" }
                Button { text: "Criar backup agora"; Layout.fillWidth: true; onClicked: appController.createBackup() }
                Label { visible: appController.backups.length === 0; text: "Nenhum backup encontrado."; color: "#667085" }
                Repeater {
                    model: appController.backups
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        Label { text: modelData.nome + " · " + modelData.tamanho_kb + " KB · " + modelData.criado_em; Layout.fillWidth: true; elide: Text.ElideRight }
                        Button { text: "Restaurar"; onClicked: confirmRestore.ask(modelData.caminho) }
                    }
                }
            }
        }
    }

    ActivityDialog { id: editDialog; parent: Overlay.overlay }
    Dialog {
        id: infoDialog; anchors.centerIn: parent; modal: true; standardButtons: Dialog.Ok
        property bool error: false
        property string text: ""
        Label { width: 420; wrapMode: Text.Wrap; text: infoDialog.text }
    }
    Dialog {
        id: confirmDelete; anchors.centerIn: parent; modal: true; title: "Excluir atividade"; standardButtons: Dialog.Yes | Dialog.No
        property int targetId: 0
        property string text: ""
        function ask(id, name) { targetId = id; text = "Excluir a atividade “" + name + "”?"; open() }
        Label { width: 380; wrapMode: Text.Wrap; text: confirmDelete.text }
        onAccepted: { appController.deleteActivity(targetId); if (window.page === 1) historyPage.applyFilter() }
    }
    Dialog {
        id: confirmRestore; anchors.centerIn: parent; modal: true; title: "Restaurar backup"; standardButtons: Dialog.Yes | Dialog.No
        property string path: ""
        function ask(value) { path = value; open() }
        Label { width: 420; wrapMode: Text.Wrap; text: "Esta operação substituirá todos os dados atuais. Deseja continuar?" }
        onAccepted: appController.restoreBackup(path)
    }
    Connections {
        target: appController
        function onMessage(title, detail, isError) { infoDialog.title = title; infoDialog.text = detail; infoDialog.error = isError; infoDialog.open() }
    }
    Component.onCompleted: reportsPage.refreshSummary()
}
