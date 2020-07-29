from PySide2.QtWidgets import QDialog
from PySide2.QtCore import Signal

from gui.ui.ui_newinstancedialog import Ui_Dialog
from gui.instancewidget import InstanceWidget

from database.linkedin import session, Client


class NewInstanceDialog(QDialog):

    newInstanceCreated = Signal(InstanceWidget)

    def __init__(self, parent):
        QDialog.__init__(self, parent=parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.mainWindow = parent
        self.ui.errorLabel.hide()

        # Load Clients
        clients = session.query(Client).all()
        for client in clients:
            self.ui.clientBox.addItem(client.name, userData=client)

    def accept(self):
        """
        Runs checks before accepting, then creates a new instance if successful
        """

        client = self.ui.clientBox.currentData()
        platform = self.ui.platformBox.currentText()

        for inst in self.mainWindow.instances.values():
            if inst.client.id == client.id and inst.platformName == platform:
                self.ui.errorLabel.setText(f"Error: A {platform} Controller is already running for {client.name}")
                self.ui.errorLabel.show()
                return

        newInst = InstanceWidget(client, platform)
        self.newInstanceCreated.emit(newInst)

        QDialog.accept(self)

    def getClient(self):
        return self.ui.clientBox.currentText()

    def getBrowser(self):
        return self.ui.browserBox.currentText()

    def getPlatform(self):
        return self.ui.platformBox.currentText()
