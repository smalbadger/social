import logging

from PySide2.QtWidgets import QWidget, QListWidgetItem, QProgressDialog, QMessageBox
from PySide2.QtCore import QThreadPool

from gui.logwidget import LogWidget
from gui.filterdialog import FilterDialog
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
        self.pwd = self.account.getPassword()
        self.profilename = self.account.profile_name

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
        self.updateStatusOfMessengerButton()

    def updateStatusOfMessengerButton(self):
        """Enable/disable the auto message button by looking at the selected connections list and the template editor"""
        enable = True

        # There must be text in the template editor
        if not self.ui.messageTemplateEdit.toPlainText().strip():
            enable = False

        # There must be connections in the selected connections list
        elif not self.ui.selectedConnectionsList.count():
            enable = False

        # TODO: Add condition that the template must be saved before sending it?

        self.ui.autoMessageButton.setEnabled(enable)

    def fetchValues(self, skipTemplates=False):
        """
        Initializes connections and then initializes templates
        """

        prog = QProgressDialog('Fetching Connections...', 'Hide', 0, 0, parent=self.window())
        prog.setModal(True)
        prog.setWindowTitle('Fetching Connections...')
        prog.show()

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

        prog.exec_()

    def fetchTemplates(self, refreshing=False):
        """
        Gets templates associated to account
        """

        self.ui.templatesBox.blockSignals(True)
        self.ui.templatesBox.clear()

        if refreshing:
            msg = 'Refreshing template list...'
        else:
            msg = 'Getting templates...'

        prog = QProgressDialog(msg, 'Hide', 0, 0, parent=self.window())
        prog.setModal(True)
        prog.setWindowTitle(msg)
        prog.show()

        def populate(templates):
            self.numTemplates = 0
            self.ui.templatesBox.clear()

            for template in templates:
                # TODO: Replace with actual template name when implemented in database
                self.numTemplates += 1
                self.addTemplate(f'Template {self.numTemplates}', template)

            if self.numTemplates != 0:
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

        prog.exec_()

    def autoMessage(self, start=True):
        """Starts or stops the messaging controller based on the status of the start/stop button."""

        # TODO: When I start, then stop the messenger manually, I get a bunch of HTTP errors. This probably needs to be
        #  fixed in the Controller class somehow so that we can safely stop at any point.

        startStopButton = self.ui.autoMessageButton

        def onComplete():
            """Called on completion of the Messenger task"""
            startStopButton.setChecked(False)
            if not self.messagingController:
                return

            startStopButton.setText("Closing, please wait...")
            startStopButton.setEnabled(False)

            self.messagingController.stop()

            del self.messagingController
            del self.messenger

            self.messagingController = None
            self.messenger = None

            startStopButton.setText("Send Message to Selected Connections")
            startStopButton.setEnabled(True)

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
            messengerBrowserOpts = self.opts[:]
            if self.ui.headlessBoxGeneral.isChecked():
                messengerBrowserOpts.append("headless")
            self.messagingController = self.controllerConstructor(self.client.name, self.email, self.pwd,
                                                                  browser=self.browser, options=messengerBrowserOpts)
            logging.getLogger(self.messagingController.getLoggerName()).addHandler(self.lw)
            self.messenger = LinkedInMessenger(self.messagingController, template,
                                               self.selectedConnections, teardown_func=onComplete)
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
        self.ui.syncButton.toggled.connect(self.synchronizeAccount)
        self.ui.selectAllBox.toggled.connect(self.selectAll)
        self.ui.saveTemplateButton.clicked.connect(self.saveCurrentTemplate)
        self.ui.newTemplateButton.clicked.connect(self.createNewTemplate)
        self.ui.templatesBox.currentIndexChanged.connect(self.loadTemplateAtIndex)
        self.ui.deleteTemplateButton.clicked.connect(lambda: self.deleteCurrentTemplate())  # lambda needed to fix bug
        self.ui.messageTemplateEdit.textChanged.connect(self.updateStatusOfMessengerButton)
        self.ui.allConnectionsList.itemClicked.connect(self.updateStatusOfMessengerButton)
        self.ui.selectedConnectionsList.itemClicked.connect(self.updateStatusOfMessengerButton)
        self.ui.selectAllBox.toggled.connect(self.updateStatusOfMessengerButton)
        self.ui.filterConnectionsButton.clicked.connect(self.openFilterDialog)

    def openFilterDialog(self):
        """
        Opens the dialog that asks for filter criteria
        """

        def filt(location, numMessages):

            def populate(filteredConnections):
                self.ui.selectedConnectionsList.clear()
                self.selectedConnections = filteredConnections
                self.ui.selectedConnectionsList.addItems(self.selectedConnections)

                prog.close()

                QMessageBox.information(self.window(), 'Connections Filtered.',
                                        f'Found {len(filteredConnections)} matching connection(s).')

            prog = QProgressDialog('Filtering Connections...', 'Hide', 0, 0, parent=self.window())
            prog.setModal(True)
            prog.setWindowTitle('Filtering...')

            task = Task(lambda: self.filterConnectionsBy(location=location, maxMessages=numMessages))
            task.finished.connect(populate)
            QThreadPool.globalInstance().start(task)

            prog.exec_()

        fd = FilterDialog(self.account, parent=self.window())
        fd.filterAccepted.connect(filt)
        fd.exec_()

    def filterConnectionsBy(self, location=None, maxMessages=10):

        result = self.allConnections

        if location:
            result = dict(filter(lambda tup: tup[1].location == location, result.items()))

        # This one is complicated:
        #  Query database for messages sent to connection from the instance's account,
        #  get the length of the returned list, and compare it to maxMessages
        result = dict(
            filter(lambda tup:
                   len(
                       list(
                           session.query(LinkedInMessage).filter(
                               LinkedInMessage.account_id == self.account.id,
                               LinkedInMessage.recipient_connection_id == tup[1].id
                           )
                       )
                   ) < maxMessages, result.items()
            )
        )

        return list(result.keys())

    def deleteCurrentTemplate(self, prompt=True):
        """
        Deletes the current template locally and then from the database
        """

        if prompt:
            ans = QMessageBox.question(self.window(), 'Confirm',
                                       "Are you sure you want to delete this template? This can't be undone.")
        else:
            ans = QMessageBox.Yes

        if ans == QMessageBox.Yes:
            def deleteTemplate():
                controller_logger.info("")
                box = self.ui.templatesBox

                template = box.currentData()
                ind = box.currentIndex()
                name = box.currentText()

                # Local deletion
                controller_logger.info(f"Deleting {name} locally...")
                box.blockSignals(True)
                box.removeItem(ind)
                self.numTemplates -= 1
                self.currentTempIndex = self.numTemplates - 1
                self.loadTemplateAtIndex(self.currentTempIndex, skipSave=True)
                box.setCurrentIndex(self.currentTempIndex)
                box.blockSignals(False)

                # Server deletion
                controller_logger.info(f"Deleting {name} from server...")
                session.delete(template)
                session.commit()

                controller_logger.info(f"Successfully deleted {name}.")

            prog = QProgressDialog('Deleting Template...', 'Hide', 0, 0, parent=self.window())
            prog.setModal(True)
            prog.setWindowTitle('Deleting...')
            prog.show()

            task = Task(deleteTemplate)
            task.finished.connect(prog.close)
            QThreadPool.globalInstance().start(task)

            prog.exec_()

    def addTemplate(self, name: str, data):
        """
        Adds a template to the template box. Naturally triggers the loadTemplateAtIndex function
        """
        self.ui.templatesBox.addItem(name, userData=data)

    def saveCurrentTemplate(self, prompt=False):
        """
        Saves the current template to the database.
        """

        template = self.ui.templatesBox.itemData(self.currentTempIndex)
        newMsg = self.ui.messageTemplateEdit.toPlainText().encode('unicode_escape')
        if template:
            curMsg = template.message_template.encode('latin1')
        else:
            curMsg = newMsg  # No need to save if there is nothing currently loaded

        # Only save if the text has been changed
        if curMsg != newMsg:

            if prompt:
                ans = QMessageBox.question(self.window(), 'Save', 'Save current template?')
            else:
                ans = QMessageBox.Yes

            if ans == QMessageBox.Yes:
                template.message_template = newMsg

                prog = QProgressDialog('Saving Template...', 'Hide', 0, 0, parent=self.window())
                prog.setModal(True)
                prog.setWindowTitle('Saving...')
                prog.show()

                task = Task(session.commit)
                task.finished.connect(prog.close)
                QThreadPool.globalInstance().start(task)

                controller_logger.info("")
                controller_logger.info(f"Saving {self.ui.templatesBox.itemText(self.currentTempIndex)}")
                prog.exec_()

        self.currentTempIndex = self.ui.templatesBox.currentIndex()

    def createNewTemplate(self, skipSave=False):
        """
        Creates a new template, and asks if the current one should be saved
        """

        # TODO: Implement QInputDialog to prompt for template name
        session.add(
            LinkedInMessageTemplate(
                account_id=self.account.id,
                message_template=" ",
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

        syncBtn = self.ui.syncButton
        def onComplete():
            """Called on completion of the Synchronizer task"""
            syncBtn.setChecked(False)
            if not self.syncController:
                return
            self.ui.syncButton.setText('Closing...')
            self.ui.syncButton.setEnabled(False)

            self.syncController.stop()

            del self.syncController
            del self.synchronizer

            self.synchronizer = None
            self.syncController = None

            self.ui.syncButton.setText('Synchronize Database')
            self.ui.syncButton.setEnabled(True)

        if checked:
            acl = self.ui.allConnectionsList
            options = {
                'messages': self.ui.updateMessagesBox.isChecked(),
                'connections': self.ui.updateConnectionsBox.isChecked(),
                'known': [acl.item(i).text() for i in range(acl.count())],
                'accept new': self.ui.newConnectionsBox.isChecked()
            }

            self.ui.tabWidget.setCurrentIndex(2)  # Go to log tab

            syncBrowserOpts = self.opts[:]
            if self.ui.headlessBoxSync.isChecked():
                syncBrowserOpts.append("headless")
            self.syncController = self.controllerConstructor(self.client.name, self.email, self.pwd,
                                                             browser=self.browser, options=syncBrowserOpts)
            logging.getLogger(self.syncController.getLoggerName()).addHandler(self.lw)

            self.synchronizer = LinkedInSynchronizer(self.syncController, options, teardown_func=onComplete)
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
        prog.exec_()

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
