from PySide2.QtWidgets import QWidget, QListWidgetItem
from gui.ui.ui_instancewidget import Ui_mainWidget
from site_controllers.linkedin import LinkedInController  # Dont delete this, used by getting it from locals dict
from fake_useragent import UserAgent

CONTROLLERS = {
    'LinkedIn': LinkedInController
}


class InstanceWidget(QWidget):

    def __init__(self, clientName, platformName):
        QWidget.__init__(self)

        self.ui = Ui_mainWidget()
        self.ui.setupUi(self)

        self.clientName = clientName
        self.platformName = platformName

        self.selectedConnections = []

        # TODO: Get credentials for client from database using their name
        controller = CONTROLLERS.get(platformName)
        email = "linkedin.test11@facade-technologies.com"
        pwd = "linkedin.test11"
        opts = [f'{UserAgent().random}']
        browser = self.ui.browserBox.currentText()
        self.controller = controller(clientName, email, pwd, browser=browser, options=opts)

        self.initializeValues()
        self.connectSignalsToFunctions()

    def initializeValues(self):
        """
        Initializes values to what is collected from the database
        """

        # TODO: Load connections and message templates. Below is an auto-generation thing
        self.ui.messageTemplateEdit.setText("yo yo {firstName}, your whole name is {fullName}, and ur a bitch")
        self.ui.templatesBox.clear()
        self.ui.templatesBox.setCurrentText("Template 1")
        self.ui.allConnectionsList.addItem("testing")
        self.ui.allConnectionsList.addItem("these")
        self.ui.allConnectionsList.addItem("cool")
        self.ui.allConnectionsList.addItem("lists")
        # Below was to test scrolling
        # self.ui.allConnectionsList.addItem("listss")
        # self.ui.allConnectionsList.addItem("listsssss")
        # self.ui.allConnectionsList.addItem("listsssssssss")
        # self.ui.allConnectionsList.addItem("listsss")
        # self.ui.allConnectionsList.addItem("lissstss")

    def connectSignalsToFunctions(self):
        """
        Connects all UI signals to functions
        """

        self.ui.allConnectionsList.itemClicked.connect(self.addContactToSelected)
        self.ui.selectedConnectionsList.itemClicked.connect(self.removeContactFromSelected)
        self.ui.autoMessageButton.clicked.connect(self.sendMessageToAll)
        self.ui.headlessBoxGeneral.toggled.connect(self.checkGeneralHeadless)
        

    def addContactToSelected(self, connection: QListWidgetItem):
        """Adds item to selected column, and updates local list"""
        if connection.text() not in self.selectedConnections:
            self.ui.selectedConnectionsList.addItem(QListWidgetItem(connection.text()))
            # self.ui.selectedConnectionsList.update()
            self.selectedConnections.append(connection.text())

    def removeContactFromSelected(self, connection: QListWidgetItem):
        """Removes connection from selected connections"""
        if connection.text() in self.selectedConnections:
            ind = self.ui.selectedConnectionsList.row(connection)
            self.ui.selectedConnectionsList.takeItem(ind)
            self.selectedConnections.remove(connection.text())

    def checkGeneralHeadless(self, checked):
        """Handles changing the headless mode on the controller's browser"""

        if checked:
            self.controller.options.headless = True
        elif "--headless" in self.controller.options:
            self.controller.options.headless = False

    def sendMessageToAll(self):
        """Calls function to send messages to all, deactivates tabs, and sets tab to logger"""

        self.ui.messagingTab.setEnabled(False)
        self.ui.syncTab.setEnabled(False)
        self.ui.tabWidget.setCurrentIndex(2)  # 2 is the logger

        self.controller.messageAll(self.selectedConnections, self.ui.messageTemplateEdit.toPlainText())
