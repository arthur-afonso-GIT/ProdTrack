import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: root
    property int activityId: 0
    width: 520
    modal: true
    anchors.centerIn: parent
    title: "Editar atividade"
    standardButtons: Dialog.NoButton

    function openActivity(id) {
        const item = appController.activity(id)
        activityId = id
        day.text = item.date || ""
        activity.text = item.name || ""
        hours.text = item.hours || "0"
        minutes.text = item.minutes || "0"
        start.text = item.start || ""
        end.text = item.end || ""
        evidence.text = item.evidence || ""
        notes.text = item.notes || ""
        open()
    }

    contentItem: ColumnLayout {
        spacing: 10
        Label { text: "Data" }
        TextField { id: day; Layout.fillWidth: true; placeholderText: "dd/mm/aaaa" }
        Label { text: "Atividade" }
        TextField { id: activity; Layout.fillWidth: true }
        Label { text: "Duração" }
        RowLayout {
            Layout.fillWidth: true
            TextField { id: hours; Layout.fillWidth: true; placeholderText: "Horas"; inputMethodHints: Qt.ImhDigitsOnly }
            Label { text: "h" }
            TextField { id: minutes; Layout.fillWidth: true; placeholderText: "Minutos"; inputMethodHints: Qt.ImhDigitsOnly }
            Label { text: "min" }
        }
        Label { text: "Horário (opcional — calcula a duração)" }
        RowLayout {
            Layout.fillWidth: true
            TextField { id: start; Layout.fillWidth: true; placeholderText: "Início  HH:MM"; maximumLength: 5 }
            Label { text: "até" }
            TextField { id: end; Layout.fillWidth: true; placeholderText: "Término  HH:MM"; maximumLength: 5 }
        }
        Label { text: "Evidência" }
        TextField { id: evidence; Layout.fillWidth: true }
        Label { text: "Observações" }
        TextArea { id: notes; Layout.fillWidth: true; Layout.preferredHeight: 80; wrapMode: TextEdit.Wrap }
        RowLayout {
            Layout.fillWidth: true
            Button { text: "Cancelar"; Layout.fillWidth: true; onClicked: root.close() }
            Button {
                text: "Salvar alterações"
                highlighted: true
                Layout.fillWidth: true
                onClicked: if (appController.updateActivity(root.activityId, day.text, activity.text,
                                                              hours.text, minutes.text, start.text, end.text,
                                                              evidence.text, notes.text)) root.close()
            }
        }
    }
}
