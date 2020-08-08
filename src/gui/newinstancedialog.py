from PySide2.QtWidgets import QDialog, QProgressDialog
from PySide2.QtCore import Signal, QThreadPool

from gui.ui.ui_newinstancedialog import Ui_Dialog
from gui.instancewidget import InstanceWidget
from gui.newclientdialog import NewClientDialog

from common.threading import Task
from database.general import session, Client
from site_controllers.linkedin import LinkedInController


class NewInstanceDialog(QDialog):

    newInstanceCreated = Signal(InstanceWidget)

    def __init__(self, parent):
        QDialog.__init__(self, parent=parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.mainWindow = parent
        self.ui.errorLabel.hide()

        self.ui.newClientButton.clicked.connect(self.newClient)
        self.ui.clientBox.activated.connect(self.populatePlatforms)
        self.ui.platformBox.setEnabled(False)

        self.ui.clientBox.activated.connect(self.ui.errorLabel.hide)
        self.ui.platformBox.activated.connect(self.ui.errorLabel.hide)

        self.populateClients()

    def newClient(self):
        """Gives the user a chance to create a new client and link accounts"""
        newClientDialog = NewClientDialog()
        newClientDialog.exec_()
        newClientDialog.clientCreated.connect(self.populateClient)

    def populateClient(self, client):
        """Adds a single client to the client combo box"""
        self.ui.clientBox.addItem(client.name, userData=client)

    def populateClients(self):
        """Fetches all clients from the database and populates the client combo box with them"""
        prog = QProgressDialog("Fetching clients, please wait...", "Hide", 0, 0, parent=self)
        prog.setModal(True)
        prog.show()

        def populate(clients):
            for client in clients:
                self.populateClient(client)
            prog.close()

        task = Task(session.query(Client).all)
        task.finished.connect(populate)
        QThreadPool.globalInstance().start(task)
        self.show()
        prog.exec_()

    def populatePlatforms(self):
        """Populates the platform combo box with the account types owned by the currently selected client"""

        client = self.ui.clientBox.currentData()
        self.ui.platformBox.clear()
        self.ui.platformBox.setEnabled(False)

        if client.linkedin_account:
            self.ui.platformBox.addItem("LinkedIn", LinkedInController)
            self.ui.platformBox.setEnabled(True)

        # TODO: Add other platform types as they become supported.

    def accept(self):
        """
        Runs checks before accepting, then creates a new instance if successful
        """

        self.ui.errorLabel.hide()
        errors = []

        client = self.ui.clientBox.currentData()
        platform = self.ui.platformBox.currentData()
        platformName = self.ui.platformBox.currentText()

        if not client:
            errors.append("Select a client")
        if not platform:
            errors.append("Select a platform or select a client that has available accounts")

        if errors:
            self.ui.errorLabel.setText("\n".join(errors))
            self.ui.errorLabel.show()
            return

        for inst in self.mainWindow.instances.values():
            if inst.client.id == client.id and inst.platformName == platformName:
                errors.append(f"Error: A {platformName} instance is already running for {client.name}")
                break

        if errors:
            self.ui.errorLabel.setText("\n".join(errors))
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
