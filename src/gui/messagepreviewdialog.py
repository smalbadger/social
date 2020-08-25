from PySide2.QtWidgets import QDialog, QListWidgetItem, QDialogButtonBox, QMessageBox
from PySide2.QtGui import Qt, QIcon

from database.general import Session
from database.linkedin import LinkedInConnection, LinkedInMessageTemplate

from gui.ui.ui_messagepreviewdialog import Ui_Dialog
from gui.templateeditwidget import TemplateEditWidget


APPROVED = 1
UNAPPROVED = 2
INVALID = 3
ALREADY_SENT = 4


class MessagePreviewDialog(QDialog):

    def __init__(self, parent, targetedConnections, template):
        QDialog.__init__(self, parent=parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        connections = [conn.id for conn in targetedConnections]
        self.targetedConnections = Session.query(LinkedInConnection)\
            .filter(LinkedInConnection.id.in_(connections))\
            .limit(100)\
            .from_self()\
            .order_by(LinkedInConnection.name)
        self.messageStatuses = {connection: None for connection in self.targetedConnections}
        self.template = Session.query(LinkedInMessageTemplate).get(template.id)

        newTemplateEdit = TemplateEditWidget(spellCheckEnabled=False, placeholderEnabled=False)
        newTemplateEdit.setReadOnly(True)
        self.ui.messagePreviewEdit.hide()
        self.ui.verticalLayout.replaceWidget(self.ui.messagePreviewEdit, newTemplateEdit)
        self.ui.messagePreviewEdit = newTemplateEdit

        self.ui.targetedConnectionsList.currentItemChanged.connect(self.onChange)

        firstInvalidMessage = None
        firstMessage = None
        self.targetedConnectionsExist = False
        for connection in self.targetedConnections:
            self.targetedConnectionsExist = True
            item = QListWidgetItem()
            item.setText(connection.name)
            item.setData(Qt.UserRole, connection)

            if not firstMessage:
                firstMessage = item

            if self.template.id in [message.template_id for message in connection.messages]:
                self.messageStatuses[connection] = ALREADY_SENT
                item.setIcon(QIcon(":/icon/resources/icons/disclaimer.png"))

            elif not self.template.isValid(connection):
                self.messageStatuses[connection] = INVALID
                item.setIcon(QIcon(":/icon/resources/icons/error.png"))

                if firstInvalidMessage is None:
                    firstInvalidMessage = item

            else:
                self.messageStatuses[connection] = UNAPPROVED
                item.setIcon(QIcon(":/icon/resources/icons/warning.png"))

            self.ui.targetedConnectionsList.addItem(item)

        # select the first message that is invalid to show the operator what might be wrong.
        if firstInvalidMessage:
            selectedItem = firstInvalidMessage
        else:
            selectedItem = firstMessage

        self.ui.targetedConnectionsList.setCurrentItem(selectedItem)
        self.populateMessagePreview()

        self.show()

        if self.allMessagesAreInvalid():
            self.ui.buttonBox.button(QDialogButtonBox.Yes).setEnabled(False)
            QMessageBox.critical(self.window(), "Invalid Messages", "This message is undeliverable to all selected connections.")


        elif self.allMessagesHaveBeenSent():
            QMessageBox.critical(self.window(), "Already Sent", "This message has already been sent to each targeted connection.")

        elif self.containsInvalidMessages():
            numInvalidMessages = self.invalidCount()
            QMessageBox.warning(self.window(), "Invalid Messages",
                                f"This message is undeliverable to {numInvalidMessages} connections "
                                f"because some placeholders could not be properly replaced. The message will not be"
                                f"sent to the connections where the message is invalid.")

    def populateMessagePreview(self):

        message = ""
        prefix = ""
        suffix = ""

        if not self.targetedConnectionsExist:
            pass
        else:
            connection = self.ui.targetedConnectionsList.currentItem().data(Qt.UserRole)
            message = self.template.fill(connection)

            if self.messageStatuses[connection] == ALREADY_SENT:
                prefix = "ALREADY SENT:"
            elif self.messageStatuses[connection] == INVALID:
                prefix = "INVALID:"

        if prefix:
            prefix = f'<span style="color: cyan"><strong>{prefix}</strong></span><br><br>'
        self.ui.messagePreviewEdit.setText(f"{prefix}{message}{suffix}")

    def onChange(self, currentItem, previousItem):

        def approve(item):
            connection = item.data(Qt.UserRole)
            status = self.messageStatuses[connection]
            if status == UNAPPROVED:
                self.messageStatuses[connection] = APPROVED
                item.setIcon(QIcon(":/icon/resources/icons/checkmark.png"))

        if currentItem:
            approve(currentItem)
        if previousItem:
            approve(previousItem)

        self.populateMessagePreview()

    def invalidCount(self):
        count = 0
        for status in self.messageStatuses.values():
            if status == INVALID:
                count += 1
        return count

    def containsInvalidMessages(self):
        for status in self.messageStatuses.values():
            if status == INVALID:
                return True
        return False

    def allMessagesAreInvalid(self):
        for status in self.messageStatuses.values():
            if status != INVALID:
                return False
        return True

    def allMessagesHaveBeenSent(self):
        for status in self.messageStatuses.values():
            if status != ALREADY_SENT:
                return False
        return True

    def containsValidConnectionMessage(self):
        for status in self.messageStatuses.values():
            if status == APPROVED or status == UNAPPROVED:
                return True
        return False