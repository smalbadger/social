import logging

from PySide2.QtWidgets import QWidget, QListWidgetItem, QProgressDialog, QMessageBox
from PySide2.QtCore import QThreadPool

from gui.logwidget import LogWidget
from gui.ui.ui_instancewidget import Ui_mainWidget

from site_controllers.linkedin import LinkedInMessenger, LinkedInSynchronizer
from fake_useragent import UserAgent
from common.strings import fromHTML, toHTML
from common.threading import Task
from common.logging import controller_logger
from database.linkedin import *


class InstanceWidget(QWidget):

    def __init__(self, client: Client, cConstructor):
        QWidget.__init__(self)

        self.ui = Ui_mainWidget()
        self.ui.setupUi(self)

        # Client info
        self.client = client
        self.platformName = cConstructor.__name__[:-len('Controller')]
        if self.platformName == 'LinkedIn':
            self.account = client.linkedin_account
        else:
            self.account = None  # TODO: update when new platforms are available

        # Account info
        self.email = self.account.email
        self.pwd = self.account.password
        self.profilename = self.account.username

        # Browser
        self.opts = [f'{UserAgent().random}']
        self.browser = self.ui.browserBox.currentText()

        # Controllers and tasks
        self.controllerConstructor = cConstructor
        self.messagingController = None
        self.messenger = None
        self.selectedConnections = []
        self.allConnections = {}
        self.syncController = None
        self.synchronizer = None

        # Logger
        self.lw = LogWidget(self.ui.instanceLogTextEdit)
        self.lw.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.lw.setLevel(logging.DEBUG)

        # Populate and initialize values
        self.numTemplates = 0
        self.currentTempIndex = -1
        self.fetchValues()

        # If critical login info is not available, disable headless mode.
        headlessEnabled = True
        for field in cConstructor.CRITICAL_LOGIN_INFO:
            if not self.account.__getattribute__(field):
                headlessEnabled = False
                break
        self.ui.headlessBoxSync.setChecked(headlessEnabled)
        self.ui.headlessBoxSync.setEnabled(headlessEnabled)
        self.ui.headlessBoxGeneral.setChecked(headlessEnabled)
        self.ui.headlessBoxGeneral.setEnabled(headlessEnabled)

        # Final stuff
        self.connectSignalsToFunctions()
        self.ui.errorLabel.hide()
        controller_logger.info(f'{self.platformName} instance created for {self.client.name}')

    def fetchValues(self, skipTemplates=False):
        """
        Initializes connections and then initializes templates
        """

        prog = QProgressDialog('Fetching Connections...', 'Hide', 0, 0, parent=self.window())
        prog.setModal(True)
        prog.setWindowTitle('Fetching Connections...')

        def populate(connections):
            self.ui.allConnectionsList.clear()
            self.ui.selectedConnectionsList.clear()
            self.selectedConnections = []

            for con in connections:
                self.ui.allConnectionsList.addItem(con.name)
                self.allConnections[con.name] = con

            prog.close()

            if not skipTemplates:
                self.fetchTemplates()

        task = Task(lambda: session.query(LinkedInConnection)
                    .filter(LinkedInConnection.account_id == self.account.id))
        task.finished.connect(populate)
        QThreadPool.globalInstance().start(task)

        prog.show()

    def fetchTemplates(self, refreshing=False):
        """
        Gets templates associated to account
        """

        self.ui.templatesBox.clear()

        if refreshing:
            msg = 'Refreshing template list...'
        else:
            msg = 'Getting templates...'

        prog = QProgressDialog(msg, 'Hide', 0, 0, parent=self.window())
        prog.setModal(True)
        prog.setWindowTitle(msg)

        def populate(templates):
            self.numTemplates = 0
            self.ui.templatesBox.clear()
            self.ui.templatesBox.blockSignals(True)

            for template in templates:
                # TODO: Replace with actual template name when implemented in database
                self.numTemplates += 1
                self.addTemplate(f'Template {self.numTemplates}', template)

            if self.numTemplates is not 0:
                # Loads the last template
                self.currentTempIndex = self.numTemplates-1
                self.ui.templatesBox.setCurrentIndex(self.currentTempIndex)
                self.loadTemplateAtIndex(self.currentTempIndex, skipSave=True)
            else:
                self.createNewTemplate(skipSave=True)

            self.ui.templatesBox.blockSignals(False)
            prog.close()

        task = Task(lambda: session.query(LinkedInMessageTemplate)
                    .filter(LinkedInMessageTemplate.account_id == self.account.id))
        task.finished.connect(populate)
        QThreadPool.globalInstance().start(task)

        prog.show()

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
            self.messagingController = self.controllerConstructor(self.client.name, self.email, self.pwd,
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
        self.ui.syncButton.toggled.connect(self.synchronizeAccount)
        self.ui.selectAllBox.toggled.connect(self.selectAll)
        self.ui.saveTemplateButton.clicked.connect(self.saveCurrentTemplate)
        self.ui.newTemplateButton.clicked.connect(self.createNewTemplate)
        self.ui.templatesBox.currentIndexChanged.connect(self.loadTemplateAtIndex)

    def addTemplate(self, name: str, data):
        """
        Adds a template to the template box. Naturally triggers the loadTemplateAtIndex function
        """
        self.ui.templatesBox.addItem(name, userData=data)

    def saveCurrentTemplate(self, prompt=False):
        """
        Saves the current template to the database.
        """

        if prompt:
            ans = QMessageBox.question(self.window(), 'Save', 'Save current template?')
        else:
            ans = QMessageBox.Yes

        if ans == QMessageBox.Yes:
            template = self.ui.templatesBox.itemData(self.currentTempIndex)
            template.message_template = self.ui.messageTemplateEdit.toPlainText().encode('unicode_escape')

            prog = QProgressDialog('Saving Template...', 'Hide', 0, 0, parent=self.window())
            prog.setModal(True)
            prog.setWindowTitle('Saving...')

            task = Task(session.commit)
            task.finished.connect(prog.close)
            QThreadPool.globalInstance().start(task)

            prog.show()

        self.currentTempIndex = self.ui.templatesBox.currentIndex()

    def createNewTemplate(self, skipSave=False):
        """
        Creates a new template, and asks if the current one should be saved
        """

        # TODO: Implement QInputDialog to prompt for template name
        session.add(
            LinkedInMessageTemplate(
                account_id=self.account.id,
                message_template="",
                crc=-1
            )
        )  # Defaulting crc to -1

        if not skipSave:
            self.saveCurrentTemplate(prompt=True)

        self.fetchTemplates(refreshing=True)

    def loadTemplateAtIndex(self, index: int, skipSave=False):
        """
        Loads template from the template at index "index" in the template choosing box,
        asking to save current one beforehand
        """

        if not skipSave:
            self.saveCurrentTemplate(prompt=True)
        
        # Encode text from db into bytes, then decode into unicode from unicode_escape
        text = self.ui.templatesBox.itemData(index).message_template.encode('latin1').decode('unicode_escape')
        self.ui.messageTemplateEdit.setPlainText(text)

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
            acl = self.ui.allConnectionsList
            options = {
                'messages': self.ui.updateMessagesBox.isChecked(),
                'connections': self.ui.updateConnectionsBox.isChecked(),
                'known': [acl.item(i).text() for i in range(acl.count())],
                'accept new': self.ui.newConnectionsBox.isChecked()
            }

            self.ui.tabWidget.setCurrentIndex(2)  # Go to log tab

            syncBrowserOpts = self.opts
            if self.ui.headlessBoxSync.isChecked():
                syncBrowserOpts.append("headless")
            self.syncController = self.controllerConstructor(self.client.name, self.email, self.pwd,
                                                             browser=self.browser, options=syncBrowserOpts)
            logging.getLogger(self.syncController.getLoggerName()).addHandler(self.lw)

            self.synchronizer = LinkedInSynchronizer(self.syncController, options, teardown_func=teardown)
            self.syncController.connectionsScraped.connect(self.scrapedConnectionsHandler)

            QThreadPool.globalInstance().start(self.synchronizer)

            self.ui.syncButton.setText('Stop')
        else:
            if self.synchronizer:
                try:
                    QThreadPool.globalInstance().cancel(self.synchronizer)
                except RuntimeError as e:
                    self.syncController.warning(str(e))
            onComplete()

    def scrapedConnectionsHandler(self, conns: dict):
        """Clears the all connections list and selected list, and fills the all connections list with new ones"""

        prog = QProgressDialog('Processing Collected Data...', 'Hide', 0, 0, parent=self.window())
        prog.setModal(True)
        prog.setWindowTitle("Processing...")
        prog.show()

        task = Task(lambda: processScrapedConnections(conns, self.account))
        task.finished.connect(prog.close)
        task.finished.connect(lambda: self.fetchValues(skipTemplates=True))
        QThreadPool.globalInstance().start(task)

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


#######################################
# Database stuff (Call these in Tasks)
#######################################

def processScrapedConnections(conns: dict, account):
    """
    - Pulls connections from DB, finds the ones that correlate to entries in conns, and updates them.
    - If there are new connections, adds them to the database.
    - Pulls again from database after getting updated and checks that new connections were added successfully
    - If not, they get logged as errors.
    - Finally, UI gets updated with newly pulled list of connections.
    """

    prev = session.query(LinkedInConnection).filter(LinkedInConnection.account_id == account.id)

    # Iterate through all connections scraped
    controller_logger.info('')
    controller_logger.info('Adding/updating collected data in database...')
    for name in conns.keys():
        alreadyExists = False
        conDict = conns[name]

        # These get defaulted in the controllers, and can't be re-defaulted without lots of if statements
        link = conDict.get('link')
        position = conDict.get('position')
        location = conDict.get('location')
        # mutual = conDict.get('mutual')

        # First look for connections to update
        for prevCon in prev:
            if prevCon.url == link:
                alreadyExists = True

                if link != prevCon.url:
                    prevCon.url = link

                if position != prevCon.position:
                    prevCon.position = position

                if location != prevCon.location:
                    prevCon.location = location

                # TODO: Implement mutual connections in database, if necessary

                break

        if alreadyExists:
            session.commit()
            continue

        # Now we know it is a new connection

        session.add(
            LinkedInConnection(
                name=name,
                account=account,
                url=link,
                location=location,
                position=position
            )
        )

        session.commit()

    # Now make sure all connections were added successfully
    for name in conns.keys():
        conDict = conns[name]
        link = conDict['link']
        # Only need to check if the new row was made. Filtering by link because it is unique
        entry = session.query(LinkedInConnection).filter(LinkedInConnection.url == link)[0]

        if not entry:
            # Should only happen if there is an error adding a new connection
            controller_logger.error(f'{name} could not be added to the database.')

        elif conDict['location'] != entry.location or conDict['position'] != entry.position:
            # For updated connections
            controller_logger.error(f'{name} could not be updated.')

    # Then return with nothing since the fetchValues function will be called again
    controller_logger.info('Done')
    controller_logger.info('')
