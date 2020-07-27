import logging

from PySide2.QtWidgets import QWidget, QListWidgetItem
from PySide2.QtCore import QThreadPool

from gui.logwidget import LogWidget
from gui.ui.ui_instancewidget import Ui_mainWidget

from site_controllers.linkedin import LinkedInController, LinkedInMessenger, LinkedInSynchronizer
from fake_useragent import UserAgent
from common.strings import fromHTML

CONTROLLERS = {
    'LinkedIn': LinkedInController
}


class InstanceWidget(QWidget):

    def __init__(self, clientName, platformName):
        QWidget.__init__(self)

        self.ui = Ui_mainWidget()
        self.ui.setupUi(self)

        self.platformName = platformName
        self.clientName = clientName
        self.email = ""
        self.password = ""
        self.ui.errorLabel.hide()

        lw = LogWidget(self.ui.instanceLogTextEdit)
        lw.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        lw.setLevel(logging.DEBUG)

        self.selectedConnections = []

        # TODO: These credentials need to be obtained elsewhere instead of hard-coding. This is just for testing
        #  purposes.
        controller = CONTROLLERS.get(platformName)
        email = "linkedin.test11@facade-technologies.com"
        pwd = "linkedin.test11"
        opts = [f'{UserAgent().random}']
        browser = self.ui.browserBox.currentText()

        self.messagingController = controller(clientName, email, pwd, browser=browser, options=opts)
        logging.getLogger(self.messagingController.getLoggerName()).addHandler(lw)
        self.messenger = None

        self.syncController = controller(clientName, email, pwd, browser=browser, options=opts)
        logging.getLogger(self.syncController.getLoggerName()).addHandler(lw)
        self.synchronizer = None

        self.initializeValues()
        self.connectSignalsToFunctions()

    def initializeValues(self):
        """
        Initializes values to what is collected from the database
        """

        # TODO: Load connections and message templates. Below is an auto-generation thing
        self.ui.messageTemplateEdit.setPlainText("yo yo {firstName}, your whole name is {fullName}\n\n YEEEET")
        self.ui.templatesBox.clear()
        self.ui.templatesBox.setCurrentText("Template 1")
        self.ui.allConnectionsList.addItems(["Mary-Ann Johnson", "Bobby Tables", "George d'tousla canil-bater"])

    def autoMessage(self, start=True):
        """Starts or stops the messaging controller based on the status of the start/stop button."""

        # TODO: When I start, then stop the messenger manually, I get a bunch of HTTP errors. This probably needs to be
        #  fixed in the Controller class somehow so that we can safely stop at any point.

        startStopButton = self.ui.autoMessageButton

        def onComplete():
            self.messenger = None
            startStopButton.setText("Closing, please wait...")
            if self.ui.closeBrowserBox.isChecked():
                self.messagingController.stop()
            startStopButton.setText("Send Message to Selected Connections")

            self.ui.startButton.setEnabled(True)
            self.ui.stopButton.setEnabled(False)

        def teardown():  # This will naturally call onComplete, otherwise it is called twice
            startStopButton.setChecked(False)

        if start:
            template = self.ui.messageTemplateEdit.toPlainText()

            if fromHTML(template) != template:
                self.ui.errorLabel.setText("Error: Template cannot use HTML reserved expressions.")
                self.ui.errorLabel.show()
                startStopButton.setChecked(False)
                return

            self.ui.startButton.setEnabled(False)
            self.ui.stopButton.setEnabled(True)
            self.ui.tabWidget.setCurrentIndex(2)  # Go to log tab

            self.ui.errorLabel.hide()
            self.messenger = LinkedInMessenger(self.messagingController, template,
                                               self.selectedConnections, teardown_func=teardown)
            QThreadPool.globalInstance().start(self.messenger)
            startStopButton.setText("Stop")
        else:
            if self.messenger:
                QThreadPool.globalInstance().cancel(self.messenger)
            onComplete()

    def connectSignalsToFunctions(self):
        """
        Connects all UI signals to functions
        """

        self.ui.autoMessageButton.clicked.connect(self.autoMessage)
        self.ui.allConnectionsList.itemClicked.connect(self.addContactToSelected)
        self.ui.selectedConnectionsList.itemClicked.connect(self.removeContactFromSelected)
        self.ui.headlessBoxGeneral.toggled.connect(self.checkGeneralHeadless)
        self.ui.startButton.clicked.connect(self.messagingController.start)
        self.ui.startButton.clicked.connect(lambda: self.ui.stopButton.setEnabled(True))
        self.ui.startButton.clicked.connect(lambda: self.ui.startButton.setEnabled(False))
        self.ui.stopButton.clicked.connect(self.messagingController.stop)
        self.ui.stopButton.clicked.connect(lambda: self.ui.stopButton.setEnabled(False))
        self.ui.stopButton.clicked.connect(lambda: self.ui.startButton.setEnabled(True))
        self.ui.syncButton.setCheckable(True)
        self.ui.syncButton.toggled.connect(self.synchronizeAccount)
        self.ui.selectAllBox.toggled.connect(self.selectAll)

    def selectAll(self, checked):
        """Selects all connections to send them a message"""
        sel = self.ui.selectedConnectionsList
        alc = self.ui.allConnectionsList

        if checked:
            sel.clear()

            items = []
            for x in range(alc.count()):
                items.append(alc.item(x))
            self.selectedConnections = [item.text() for item in items]

            sel.addItems(self.selectedConnections)

            sel.setEnabled(False)
        else:
            sel.clear()
            self.selectedConnections = []
            sel.setEnabled(True)

    def synchronizeAccount(self, checked):
        """Synchronizes account using options given in GUI"""

        def onComplete():
            self.connector = None
            self.ui.syncButton.setText('Closing...')
            self.syncController.stop()
            self.ui.syncButton.setText('Synchronize Database')

        def teardown():  # This will naturally call onComplete, otherwise it is called twice
            self.ui.syncButton.setChecked(False)

        if checked:
            options = {
                'headless': self.ui.headlessBoxSync.isChecked(),
                'messages': self.ui.updateMessagesBox.isChecked(),
                'connections': self.ui.updateConnectionsBox.isChecked(),
                'accept new': self.ui.newConnectionsBox.isChecked()
            }

            self.ui.syncButton.setText('Stop')
            self.ui.tabWidget.setCurrentIndex(2)  # Go to log tab

            self.synchronizer = LinkedInSynchronizer(self.syncController, options, teardown_func=teardown)
            QThreadPool.globalInstance().start(self.synchronizer)
        else:
            if self.synchronizer:
                QThreadPool.globalInstance().cancel(self.synchronizer)
            onComplete()

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
            self.ui.closeBrowserBox.setChecked(True)
            self.ui.closeBrowserBox.setEnabled(False)
            self.messagingController.options.headless = True
        else:
            self.ui.closeBrowserBox.setEnabled(True)
            self.messagingController.options.headless = False
