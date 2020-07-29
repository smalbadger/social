import logging

from PySide2.QtWidgets import QWidget, QListWidgetItem
from PySide2.QtCore import QThreadPool
from selenium.common.exceptions import InvalidSessionIdException

from gui.logwidget import LogWidget
from gui.ui.ui_instancewidget import Ui_mainWidget

from site_controllers.linkedin import LinkedInController, LinkedInMessenger, LinkedInSynchronizer
from fake_useragent import UserAgent
from common.strings import fromHTML


class InstanceWidget(QWidget):

    def __init__(self, client, platformName):
        QWidget.__init__(self)

        self.ui = Ui_mainWidget()
        self.ui.setupUi(self)

        self.platformName = platformName
        self.client = client
        self.ui.errorLabel.hide()

        self.lw = LogWidget(self.ui.instanceLogTextEdit)
        self.lw.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.lw.setLevel(logging.DEBUG)

        self.selectedConnections = []

        # TODO: These credentials need to be obtained elsewhere instead of hard-coding. This is just for testing
        #  purposes.
        self.controllerConstructor = globals().get(platformName + 'Controller')
        self.email = "linkedin.test11@facade-technologies.com"
        self.pwd = "linkedin.test11"
        self.opts = [f'{UserAgent().random}']
        self.browser = self.ui.browserBox.currentText()

        self.messagingController = None
        self.messenger = None

        self.syncController = None
        self.synchronizer = None

        self.initializeValues()
        self.connectSignalsToFunctions()

    def initializeValues(self):
        """
        Initializes values to what is collected from the database
        """

        # TODO: Load connections and message templates from database
        self.ui.messageTemplateEdit.setPlainText("yo yo {firstName}, your whole name is {fullName}")
        self.ui.templatesBox.clear()
        self.ui.templatesBox.setCurrentText("Template 1")
        self.ui.allConnectionsList.addItems(["Mary-Ann Johnson", "Bobby Tables", "George d'tousla canil-bater"])

    def autoMessage(self, start=True):
        """Starts or stops the messaging controller based on the status of the start/stop button."""

        # TODO: When I start, then stop the messenger manually, I get a bunch of HTTP errors. This probably needs to be
        #  fixed in the Controller class somehow so that we can safely stop at any point.

        startStopButton = self.ui.autoMessageButton

        def onComplete():
            startStopButton.setText("Closing, please wait...")
            startStopButton.setEnabled(False)

            self.messagingController.stop()

            del self.messagingController
            del self.messenger

            self.messagingController = None
            self.messenger = None

            startStopButton.setText("Send Message to Selected Connections")
            startStopButton.setEnabled(True)

        def teardown():  # This will naturally call onComplete, otherwise it is called twice
            startStopButton.setChecked(False)

        if start:
            template = self.ui.messageTemplateEdit.toPlainText()

            if fromHTML(template) != template:
                self.ui.errorLabel.setText("Error: Template cannot use HTML reserved expressions.")
                self.ui.errorLabel.show()
                startStopButton.setChecked(False)
                return

            # GUI Stuff
            self.ui.errorLabel.hide()
            self.ui.tabWidget.setCurrentIndex(2)  # Go to log tab

            # Controller stuff
            self.messagingController = self.controllerConstructor(self.clientName, self.email, self.pwd,
                                                                  browser=self.browser, options=self.opts)
            logging.getLogger(self.messagingController.getLoggerName()).addHandler(self.lw)
            self.messenger = LinkedInMessenger(self.messagingController, template,
                                               self.selectedConnections, teardown_func=teardown)
            QThreadPool.globalInstance().start(self.messenger)

            startStopButton.setText("Stop")
        else:
            if self.messenger:
                try:
                    QThreadPool.globalInstance().cancel(self.messenger)
                except RuntimeError as e:
                    self.messagingController.warning(str(e))
            onComplete()

    def connectSignalsToFunctions(self):
        """
        Connects all UI signals to functions
        """

        self.ui.autoMessageButton.toggled.connect(self.autoMessage)
        self.ui.allConnectionsList.itemClicked.connect(self.addContactToSelected)
        self.ui.selectedConnectionsList.itemClicked.connect(self.removeContactFromSelected)
        self.ui.headlessBoxGeneral.toggled.connect(self.checkGeneralHeadless)
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
            self.ui.syncButton.setText('Closing...')
            self.ui.syncButton.setEnabled(False)

            self.syncController.stop()

            del self.syncController
            del self.synchronizer

            self.synchronizer = None
            self.syncController = None

            self.ui.syncButton.setText('Synchronize Database')
            self.ui.syncButton.setEnabled(True)

        def teardown():  # This will naturally call onComplete, otherwise it is called twice
            self.ui.syncButton.setChecked(False)

        if checked:
            options = {
                'headless': self.ui.headlessBoxSync.isChecked(),
                'messages': self.ui.updateMessagesBox.isChecked(),
                'connections': self.ui.updateConnectionsBox.isChecked(),
                'accept new': self.ui.newConnectionsBox.isChecked()
            }

            self.ui.tabWidget.setCurrentIndex(2)  # Go to log tab

            self.syncController = self.controllerConstructor(self.clientName, self.email, self.pwd,
                                                             browser=self.browser, options=self.opts)
            logging.getLogger(self.syncController.getLoggerName()).addHandler(self.lw)

            self.synchronizer = LinkedInSynchronizer(self.syncController, options, teardown_func=teardown)
            self.syncController.connectionsScraped.connect(self.refreshConnections)

            QThreadPool.globalInstance().start(self.synchronizer)

            self.ui.syncButton.setText('Stop')
        else:
            if self.synchronizer:
                try:
                    QThreadPool.globalInstance().cancel(self.synchronizer)
                except RuntimeError as e:
                    self.syncController.warning(str(e))
            onComplete()

    def refreshConnections(self, conns: dict):
        """Clears the all connections list and selected list, and fills the all connections list with new ones"""

        self.ui.allConnectionsList.clear()
        self.ui.allConnectionsList.addItems(conns.keys())
        self.ui.selectedConnectionsList.clear()
        self.selectedConnections = []

    def addContactToSelected(self, connection: QListWidgetItem):
        """Adds item to selected column, and updates local list"""
        if connection.text() not in self.selectedConnections:
            self.ui.selectedConnectionsList.addItem(QListWidgetItem(connection.text()))
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
