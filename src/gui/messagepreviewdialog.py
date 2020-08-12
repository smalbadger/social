from PySide2.QtWidgets import QDialog, QListWidgetItem, QDialogButtonBox, QMessageBox
from PySide2.QtGui import Qt, QIcon

from database.general import Session
from database.linkedin import LinkedInConnection, LinkedInMessageTemplate

from gui.ui.ui_messagepreviewdialog import Ui_Dialog
from gui.templateeditwidget import TemplateEditWidget


APPROVED = 1
UNAPPROVED = 2
INVALID = 3


class MessagePreviewDialog(QDialog):

    def __init__(self, parent, targetedConnections, template):
        QDialog.__init__(self, parent=parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        connections = [conn.id for conn in targetedConnections]
        self.targetedConnections = Session.query(LinkedInConnection).filter(LinkedInConnection.id.in_(connections))
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
        for connection in self.targetedConnections:
            item = QListWidgetItem()
            item.setText(connection.name)
            item.setData(Qt.UserRole, connection)

            if not firstMessage:
                firstMessage = item

            if self.template.isValid(connection):
                self.messageStatuses[connection] = UNAPPROVED
                item.setIcon(QIcon(":/icon/resources/icons/warning.png"))
            else:
                self.messageStatuses[connection] = INVALID
                item.setIcon(QIcon(":/icon/resources/icons/error.png"))

                if firstInvalidMessage is None:
                    firstInvalidMessage = item

            self.ui.targetedConnectionsList.addItem(item)

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

        elif self.containsInvalidMessages():
            numInvalidMessages = self.invalidCount()
            QMessageBox.warning(self.window(), "Invalid Messages",
                                f"This message is undeliverable to {numInvalidMessages} connections "
                                f"because some placeholders could not be properly replaced. The message will not be"
                                f"sent to the connections where the message is invalid.")

    def populateMessagePreview(self):
        connection = self.ui.targetedConnectionsList.currentItem().data(Qt.UserRole)
        message = self.template.fill(connection)
        self.ui.messagePreviewEdit.setText(message.replace(r"\n", "\n"))

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