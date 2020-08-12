from PySide2.QtWidgets import QDialog, QProgressDialog
from PySide2.QtCore import Signal, QThreadPool

from gui.ui.ui_newinstancedialog import Ui_Dialog
from gui.instancewidget import InstanceWidget
from gui.newclientdialog import NewClientDialog

from common.threading import Task
from database.general import Session, Client
from site_controllers.linkedin import LinkedInController


class NewInstanceDialog(QDialog):

    newInstanceCreated = Signal(InstanceWidget)

    def __init__(self, parent):
        QDialog.__init__(self, parent=parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.mainWindow = parent
        self.ui.errorLabel.hide()

        self.clients = []
        self.testers = []

        self.ui.newClientButton.clicked.connect(self.newClient)
        self.ui.clientBox.activated.connect(self.populatePlatforms)
        self.ui.platformBox.setEnabled(False)

        self.ui.clientBox.activated.connect(self.ui.errorLabel.hide)
        self.ui.platformBox.activated.connect(self.ui.errorLabel.hide)
        self.ui.testAccountsBox.toggled.connect(self.updateDropdown)

        self.populateClients()
        self.ui.testAccountsBox.setChecked(True)  # TODO: Remove when making an executable
        self.populatePlatforms()

    def updateDropdown(self, withTesters: bool):
        self.ui.clientBox.clear()

        targList = self.testers if withTesters else self.clients
        print(targList)
        print(self.testers)

        for acct in targList:
            self.populateClient(acct)

        self.populatePlatforms()

    def newClient(self):
        """Gives the user a chance to create a new client and link accounts"""

        def addClient(client):
            # client = Session
            if client.tester:
                self.ui.testAccountsBox.setChecked(True)
                self.testers.append(client)
                self.updateDropdown(withTesters=True)
            else:
                self.ui.testAccountsBox.setChecked(False)
                self.clients.append(client)
                self.updateDropdown(withTesters=False)

        newClientDialog = NewClientDialog()
        newClientDialog.exec_()
        newClientDialog.clientCreated.connect(addClient)

    def populateClient(self, client):
        """Adds a single client to the client combo box"""
        self.ui.clientBox.addItem(client.name, userData=client)

    def populateClients(self):
        """Fetches all clients from the database and populates the client combo box with them"""
        prog = QProgressDialog("Fetching clients, please wait...", "Hide", 0, 0, parent=self)
        prog.setWindowTitle('Fetching clients...')
        prog.setModal(True)
        prog.show()

        def populate(clients):
            for client in clients:
                if not client.tester:
                    self.clients.append(client)
                    if not self.ui.testAccountsBox.isChecked():
                        self.populateClient(client)
                else:
                    self.testers.append(client)
                    if self.ui.testAccountsBox.isChecked():
                        self.populateClient(client)

            prog.close()

        task = Task(lambda: Session.query(Client).all())
        task.finished.connect(populate)
        QThreadPool.globalInstance().start(task)
        prog.show()
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
