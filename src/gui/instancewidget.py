import csv
import logging

from PySide2.QtWidgets import (QWidget, QListWidgetItem, QTreeWidgetItem, QProgressDialog,
                               QMessageBox, QDialog, QInputDialog, QFileDialog)
from PySide2.QtCore import QThreadPool, Signal, Qt

from gui.logwidget import LogWidget
from gui.filterdialog import FilterDialog
from gui.ui.ui_instancewidget import Ui_mainWidget
from gui.templateeditwidget import TemplateEditWidget
from gui.messagepreviewdialog import MessagePreviewDialog
from gui.searchcriteriadialog import SearchCriteriaDialog

from site_controllers.linkedin import (LinkedInMessenger, LinkedInBulkConnectionScraper, UploadConnectionCSV,
                                       LinkedInIndividualConnectionScraper, LinkedInConnectionRequestAccepter,
                                       LinkedInConnectionRequestSender)
from fake_useragent import UserAgent

from common.strings import fromHTML
from common.threading import Task

from database.linkedin import *
from database.general import Session, Client


class InstanceWidget(QWidget):

    dailyLimitChanged = Signal(int)
    actionCountChanged = Signal(int)

    # --- Initialization Methods ---------------------------------------------------------------------------------------

    def __init__(self, client: Client, cConstructor):
        QWidget.__init__(self)

        self.ui = Ui_mainWidget()
        self.ui.setupUi(self)

        newTemplateEdit = TemplateEditWidget()
        self.ui.messageTemplateEdit.hide()
        self.ui.templateLayout.replaceWidget(self.ui.messageTemplateEdit, newTemplateEdit)
        self.ui.messageTemplateEdit = newTemplateEdit

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
        self.opts = [f'{UserAgent().random}', "--disable-gpu"]
        self.browser = self.ui.browserBox.currentText()

        # Controllers and tasks
        self.controllerConstructor = cConstructor
        self.messagingController = None
        self.messenger = None
        self.selectedConnections = []
        self.allConnections = {}
        self.syncController = None
        self.synchronizer = None
        self.messagingDelayLowerBound = 5
        self.messagingDelayUpperBound = 3000

        # Loggers and handlers
        self.lw = LogWidget(self.ui.instanceLogTextEdit)
        self.lw.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.lw.setLevel(logging.DEBUG)
        self.lw.addLogger(f"gui.linkedin.{self.profilename}", "rgba(255, 100, 100, 0.2)")
        self.lw.addLogger(f"database.linkedin.{self.profilename}", "rgba(100, 100, 255, 0.2)")

        self.db_logger = logging.getLogger(f"database.linkedin.{self.profilename}")
        self.gui_logger = logging.getLogger(f"gui.linkedin.{self.profilename}")

        # Populate and initialize values
        self.ui.dailyActionLimitSpinBox.setValue(self.client.linkedin_account.getDailyActivityLimit())
        self.numTemplates = 0
        self.currentTempIndex = -1
        self.fetchValues()

        # If critical login info is not available, disable headless mode.
        headlessEnabled = True
        for field in cConstructor.CRITICAL_LOGIN_INFO:
            if not self.account.__getattribute__(field):
                headlessEnabled = False
                break
        self.ui.headlessBoxGeneral.setChecked(False)
        self.ui.headlessBoxGeneral.setEnabled(headlessEnabled)

        # Final stuff
        self.connectSignalsToFunctions()
        self.ui.errorLabel.hide()
        self.gui_logger.info(f'{self.platformName} instance created for {self.client.name}')
        self.updateStatusOfMessengerButton()

    def fetchValues(self, skipTemplates=False):
        """
        Initializes connections and then initializes templates
        """
        msg = "Fetching connections from database..."
        prog = QProgressDialog(msg, 'Hide', 0, 0, parent=self.window())
        prog.setModal(True)
        prog.setWindowTitle(msg)
        prog.show()

        def populate(connections):
            self.gui_logger.info("Populating connections...")
            self.ui.allConnectionsList.clear()
            self.ui.connectionsTable.clear()
            self.ui.selectedConnectionsList.clear()
            self.selectedConnections = []

            for con in connections:
                self.gui_logger.debug(con.name)

                # Add to connections list for messaging
                self.ui.allConnectionsList.addItem(con.name)

                # Add to main connections table
                connectionItem = QTreeWidgetItem(self.ui.connectionsTable)
                connectionItem.setText(0, con.name)
                connectionItem.setText(1, con.location)
                connectionItem.setText(2, con.position)

                self.allConnections[con.name] = con

            self.ui.allConnectionsGroupBox.setTitle(f"All Connections ({len(self.allConnections)})")

            prog.close()

            if not skipTemplates:
                self.fetchTemplates()

        self.db_logger.info(msg)
        task = Task(lambda: Session.query(LinkedInConnection)
                    .filter(LinkedInConnection.account_id == self.account.id)
                    .order_by(LinkedInConnection.name))
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

            self.gui_logger.info("Populating templates...")
            for template in templates:
                # TODO: Replace with actual template name when implemented in database
                self.gui_logger.debug(str(template.id) + ': ' + template.message_template)
                self.numTemplates += 1
                self.addTemplate(template.name.encode('latin1').decode('unicode_escape'), template)

            if self.numTemplates != 0:
                # Loads the last template
                self.currentTempIndex = self.numTemplates-1
                self.ui.templatesBox.setCurrentIndex(self.currentTempIndex)
                self.loadTemplateAtIndex(self.currentTempIndex, skipSave=True)
            else:
                self.createNewTemplate(skipSave=True)

            self.ui.templatesBox.blockSignals(False)
            prog.close()

        self.db_logger.info(msg)
        task = Task(lambda: Session.query(LinkedInMessageTemplate)
                    .filter(LinkedInMessageTemplate.account_id == self.account.id,
                            LinkedInMessageTemplate.deleted == False))
        task.finished.connect(populate)
        QThreadPool.globalInstance().start(task)

        prog.exec_()

    def connectSignalsToFunctions(self):
        """
        Connects all UI signals to functions
        """

        self.ui.acceptConnectionRequestsBtn.clicked.connect(self.acceptConnectionRequests)
        self.ui.autoMessageButton.toggled.connect(self.autoMessage)
        self.ui.allConnectionsList.itemClicked.connect(self.addConnectionToSelected)
        self.ui.selectedConnectionsList.itemClicked.connect(self.removeConnectionFromSelected)
        self.ui.scrapeBulkConnectionsBtn.toggled.connect(self.scrapeConnectionsInBulk)
        self.ui.selectAllBox.toggled.connect(self.selectAllConnections)
        self.ui.saveTemplateButton.clicked.connect(self.saveCurrentTemplate)
        self.ui.newTemplateButton.clicked.connect(self.createNewTemplate)
        self.ui.templatesBox.currentIndexChanged.connect(self.loadTemplateAtIndex)
        self.ui.deleteTemplateButton.clicked.connect(lambda: self.deleteCurrentTemplate())  # lambda needed to fix bug
        self.ui.messageTemplateEdit.textChanged.connect(self.updateStatusOfMessengerButton)
        self.ui.allConnectionsList.itemClicked.connect(self.updateStatusOfMessengerButton)
        self.ui.selectedConnectionsList.itemClicked.connect(self.updateStatusOfMessengerButton)
        self.ui.selectAllBox.toggled.connect(self.updateStatusOfMessengerButton)
        self.ui.filterConnectionsButton.clicked.connect(self.openFilterDialog)
        self.ui.uploadConnectionsCSVBtn.clicked.connect(self.parseConnectionsCSV)
        self.ui.scrapeIndividualConnectionsBtn.toggled.connect(self.scrapeConnectionsIndividually)
        self.ui.sendConnectionRequestsBtn.toggled.connect(self.sendConnectionRequests)

        # Wanted to connect to the focusOut signal, but that doesn't exist, so this is the next best thing.
        def onDailyLimitUpdated(*args):
            value = self.ui.dailyActionLimitSpinBox.value()
            self.client.linkedin_account.setActivityLimitForToday(value)
            self.dailyLimitChanged.emit(value)

        self.ui.dailyActionLimitSpinBox.focusOutEvent = onDailyLimitUpdated

        def searchConnections(partialName):
            if self.allConnections:
                results = [entry.text() for entry in self.ui.allConnectionsList.findItems(partialName, Qt.MatchContains)]
                all = self.ui.allConnectionsList.findItems('', Qt.MatchContains)

                for entry in all:
                    if entry.text() in results:
                        entry.setHidden(False)
                    else:
                        entry.setHidden(True)

        self.ui.searchBox.textEdited.connect(searchConnections)

        def updateMessagingDelay(minOrMax):
            """
            sets the delay spinboxes to valid values and then records the values in instance variables that get
            propagated to the messaging controller
            """
            if minOrMax == max:
                toUpdate = self.ui.maxMessagingDelaySpinBox
            else:
                toUpdate = self.ui.minMessagingDelaySpinBox
            currentMin = self.ui.minMessagingDelaySpinBox.value()
            currentMax = self.ui.maxMessagingDelaySpinBox.value()
            toUpdate.setValue(minOrMax(currentMin, currentMax))
            self.messagingDelayLowerBound = self.ui.minMessagingDelaySpinBox.value()
            self.messagingDelayUpperBound = self.ui.maxMessagingDelaySpinBox.value()
            if self.messagingController:
                self.messagingController.setMessageDelayRange(self.messagingDelayLowerBound, self.messagingDelayUpperBound)

        updateMessagingDelay(min)
        self.ui.minMessagingDelaySpinBox.valueChanged.connect(lambda: updateMessagingDelay(max))
        self.ui.maxMessagingDelaySpinBox.valueChanged.connect(lambda: updateMessagingDelay(min))

    # --- Messaging Methods --------------------------------------------------------------------------------------------

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

    def autoMessage(self, start=True):
        """Starts or stops the messaging controller based on the status of the start/stop button."""

        startStopButton = self.ui.autoMessageButton

        def onComplete():
            """Called on completion of the Messenger task"""
            startStopButton.setChecked(False)
            if not self.messagingController:
                return

            startStopButton.setText("Closing, please wait...")
            startStopButton.setEnabled(False)

            self.messagingController.closing = True
            self.messagingController.stop()

            del self.messagingController
            del self.messenger

            self.messagingController = None
            self.messenger = None

            startStopButton.setText("Send Message to Selected Connections")
            startStopButton.setEnabled(True)

        if start:
            self.saveCurrentTemplate()

            # NOTE: Since another thread saves different objects to the database, committing forces
            #       us to go back to the database and get the freshest version of an object
            Session.commit()
            template = self.ui.templatesBox.currentData()

            if fromHTML(template.message_template) != template.message_template:
                self.ui.errorLabel.setText("Error: Template cannot use HTML reserved expressions.")
                self.ui.errorLabel.show()
                startStopButton.setChecked(False)
                return

            # Getting query items from selected list
            connections = [self.allConnections[name] for name in self.selectedConnections]

            # Show a preview of the message and ask if the operator would like to proceed
            preview = MessagePreviewDialog(self, connections, template)
            preview.exec_()
            if preview.result() == QDialog.Rejected:
                return self.autoMessage(False)

            # GUI Stuff
            self.ui.errorLabel.hide()

            # Options
            messengerBrowserOpts = self.opts[:]
            if self.ui.headlessBoxGeneral.isChecked():
                messengerBrowserOpts.append("headless")

            # Controller
            self.messagingController = self.controllerConstructor(self.client.name, self.email, self.pwd,
                                                                  browser=self.browser, options=messengerBrowserOpts)
            self.messagingController.setMessageDelayRange(self.messagingDelayLowerBound, self.messagingDelayUpperBound)
            self.messagingController.messageSent.connect(lambda cid, mid: self.actionCountChanged.emit(cid))
            self.lw.addLogger(self.messagingController.getLoggerName(), "rgba(100, 100, 0, 0.2)")

            # Task
            self.messenger = LinkedInMessenger(self.messagingController, template,
                                               connections, teardown_func=onComplete)
            QThreadPool.globalInstance().start(self.messenger)

            startStopButton.setText("Stop")
        else:
            if self.messenger:
                try:
                    QThreadPool.globalInstance().cancel(self.messenger)
                except RuntimeError as e:
                    self.messagingController.warning(str(e))
            onComplete()

    def openFilterDialog(self):
        """
        Opens the dialog that asks for filter criteria
        """
        msg = "Filtering connections..."

        def filt(locations, numMessages):
            def populate(filteredConnections):
                self.ui.selectedConnectionsList.clear()
                self.selectedConnections = filteredConnections
                self.ui.selectedConnectionsList.addItems(self.selectedConnections)

                prog.close()

                QMessageBox.information(self.window(), 'Connections Filtered.',
                                        f'Found {len(filteredConnections)} matching connection(s).')

            prog = QProgressDialog(msg, 'Hide', 0, 0, parent=self.window())
            prog.setModal(True)
            prog.setWindowTitle(msg)
            prog.show()

            self.db_logger.info(msg)
            task = Task(lambda: self.filterConnectionsBy(locations=locations, maxMessages=numMessages))
            task.finished.connect(populate)
            QThreadPool.globalInstance().start(task)

            prog.exec_()

        fd = FilterDialog(self.account, parent=self)
        fd.filterAccepted.connect(filt)
        fd.exec_()

    def filterConnectionsBy(self, locations=(False, None), maxMessages=(False, None)):
        """
        All args are (useCriteria, value) tuples
        """

        if locations[0]:
            self.db_logger.info("Filtering by location")
            result = {}  # We add each connection with location in the location list
            for location in locations[1]:
                result.update(dict(filter(lambda tup: tup[1].location == location, self.allConnections.items())))
        else:
            result = self.allConnections

        if maxMessages[0]:
            self.db_logger.info("Filtering by max messages")
            # This one is complicated:
            #  Query database for messages sent to connection from the instance's account,
            #  get the length of the returned list, and compare it to maxMessages
            result = dict(
                filter(lambda tup:
                       len(
                           list(
                               Session.query(LinkedInMessage).filter(
                                   LinkedInMessage.account_id == self.account.id,
                                   LinkedInMessage.recipient_connection_id == tup[1].id
                               )
                           )
                       ) < maxMessages[1], result.items()
                )
            )

        return list(result.keys())

    def deleteCurrentTemplate(self, prompt=True):
        """
        Deletes the current template locally and then from the database
        """

        if prompt:
            ans = QMessageBox.question(self.window(), 'Confirm',
                                       "Are you sure you want to delete this template?")
        else:
            ans = QMessageBox.Yes

        if ans == QMessageBox.Yes:
            self.gui_logger.info("Removing current template")
            box = self.ui.templatesBox

            def deleteTemplate():
                template = box.currentData()
                ind = box.currentIndex()
                name = box.currentText()

                # Local deletion
                self.gui_logger.info(f"Deleting {name} locally...")
                box.blockSignals(True)
                box.removeItem(ind)
                self.numTemplates -= 1
                self.currentTempIndex = min(ind, self.numTemplates - 1)
                box.setCurrentIndex(self.currentTempIndex)
                box.blockSignals(False)

                # Server deletion
                self.db_logger.info(f"Deleting {name} from server...")
                template = Session.query(LinkedInMessageTemplate).get(template.id)
                template.deleted = True
                Session.commit()

                self.gui_logger.info(f"Successfully deleted {name}.")

            prog = QProgressDialog('Deleting Template...', 'Hide', 0, 0, parent=self.window())
            prog.setModal(True)
            prog.setWindowTitle('Deleting...')
            prog.show()

            task = Task(deleteTemplate)
            task.finished.connect(prog.close)
            task.finished.connect(lambda: self.loadTemplateAtIndex(box.currentIndex(), skipSave=True))
            QThreadPool.globalInstance().start(task)

            prog.exec_()

    def addTemplate(self, name: str, data):
        """
        Adds a template to the template box. Naturally triggers the loadTemplateAtIndex function
        """
        self.gui_logger.info(f"Adding {name}")
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

                def save():
                    templateObj = Session.query(LinkedInMessageTemplate).get(template.id)
                    templateObj.message_template = newMsg
                    Session.commit()

                prog = QProgressDialog('Saving Template...', 'Hide', 0, 0, parent=self.window())
                prog.setModal(True)
                prog.setWindowTitle('Saving...')
                prog.show()

                task = Task(save)
                task.finished.connect(prog.close)
                QThreadPool.globalInstance().start(task)

                self.db_logger.info(f"Saving {self.ui.templatesBox.itemText(self.currentTempIndex)}")
                prog.exec_()

        self.currentTempIndex = self.ui.templatesBox.currentIndex()

    def createNewTemplate(self, skipSave=False):
        """
        Creates a new template, and asks if the current one should be saved
        """

        name, ok = QInputDialog.getText(self.window(), 'Campaign Name',
                                    'Please enter a name for your new campaign/message template.')

        if name and ok:
            prog = QProgressDialog('Processing...', 'Hide', 0, 0, parent=self.window())
            prog.setModal(True)
            prog.setWindowTitle(f"Creating Template {name} ...")
            prog.show()

            def createTemplate():
                Session.add(
                    LinkedInMessageTemplate(
                        account_id=self.account.id,
                        name=name.encode('unicode_escape'),
                        message_template=" ",
                        crc=LinkedInMessageTemplate.defaultCRC
                    )
                )  # Defaulting crc to -1
                Session.commit()
                prog.close()
                
            QThreadPool.globalInstance().start(Task(createTemplate))
            prog.exec_()

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

        template = self.ui.templatesBox.itemData(index)
        if template:
            text = template.message_template.encode('latin1').decode('unicode_escape')
            self.ui.messageTemplateEdit.setPlainText(text)
        else:
            self.createNewTemplate(skipSave=True)

    def selectAllConnections(self, checked):
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

    def addConnectionToSelected(self, connection: QListWidgetItem):
        """Adds item to selected column, and updates local list"""
        if connection.text() not in self.selectedConnections:
            self.ui.selectedConnectionsList.addItem(QListWidgetItem(connection.text()))
            self.selectedConnections.append(connection.text())

    def removeConnectionFromSelected(self, connection: QListWidgetItem):
        """Removes connection from selected connections"""
        if connection.text() in self.selectedConnections:
            ind = self.ui.selectedConnectionsList.row(connection)
            self.ui.selectedConnectionsList.takeItem(ind)
            self.selectedConnections.remove(connection.text())

    # --- Connections Methods ------------------------------------------------------------------------------------------

    def parseConnectionsCSV(self):
        """
        Opens a file dialog for the user to select the csv file, then it parses it and creates connections for them
        """

        self.ui.scrapeIndividualConnectionsBtn.setEnabled(False)
        self.ui.scrapeBulkConnectionsBtn.setEnabled(False)
        self.ui.acceptConnectionRequestsBtn.setEnabled(False)
        self.ui.sendConnectionRequestsBtn.setEnabled(False)

        url = QFileDialog.getOpenFileUrl(filter='Comma Separated Values (*.csv)')[0].toString()

        if url:
            with open(url[len('file:///'):], 'r', newline='', encoding='utf-8') as csvfile:
                connections = list(csv.reader(csvfile))

            if connections[0][0] != 'First Name':
                QMessageBox.warning(self.window(), 'Invalid File', 'Not a valid CSV file.')
                self.ui.scrapeIndividualConnectionsBtn.setEnabled(True)
                self.ui.scrapeBulkConnectionsBtn.setEnabled(True)
                return

            connections.pop(0)

            prog = QProgressDialog('Parsing CSV and uploading to database...', 'Hide',
                                   0, round(len(connections)/10), self.window())
            prog.setWindowTitle('Uploading CSV...')
            prog.setValue(0)
            prog.setModal(True)

            uc = UploadConnectionCSV(self.account.id, connections)
            uc.packageCommitted.connect(lambda: prog.setValue(prog.value()+1))

            def cleanup(num):
                prog.close()
                self.ui.scrapeIndividualConnectionsBtn.setEnabled(True)
                self.ui.scrapeBulkConnectionsBtn.setEnabled(True)
                # For some reason can't log from this, so just printing the message
                print(f'Skipped {num} connections because their csv entries were blank.')

            uc.finished.connect(cleanup)
            QThreadPool.globalInstance().start(uc)

            prog.exec_()

            self.fetchValues()

    def scrapeConnectionsInBulk(self, checked):
        """Synchronizes account using options given in GUI"""

        btn = self.ui.scrapeBulkConnectionsBtn
        originalText = btn.text()

        def onComplete():
            """Called on completion of the Synchronizer task"""

            btn.setChecked(False)
            if not self.syncController:
                return
            btn.setText('Closing...')
            btn.setEnabled(False)

            self.syncController.closing = True
            self.syncController.stop()

            del self.syncController
            del self.synchronizer

            self.synchronizer = None
            self.syncController = None

            btn.setText(originalText)
            btn.setEnabled(True)
            self.ui.scrapeIndividualConnectionsBtn.setEnabled(True)
            self.ui.uploadConnectionsCSVBtn.setEnabled(True)
            self.ui.acceptConnectionRequestsBtn.setEnabled(True)
            self.ui.sendConnectionRequestsBtn.setEnabled(True)

        if checked:
            self.ui.scrapeIndividualConnectionsBtn.setEnabled(False)
            self.ui.uploadConnectionsCSVBtn.setEnabled(False)
            self.ui.acceptConnectionRequestsBtn.setEnabled(False)
            self.ui.sendConnectionRequestsBtn.setEnabled(False)

            known = [name[0] for name in
                     Session.query(LinkedInConnection.name).filter(LinkedInConnection.account_id == self.account.id)]

            options = {
                'known': known,
                'accid': self.account.id
            }

            syncBrowserOpts = self.opts[:]
            if self.ui.headlessBoxGeneral.isChecked():
                syncBrowserOpts.append("headless")
            self.syncController = self.controllerConstructor(self.client.name, self.email, self.pwd,
                                                             browser=self.browser, options=syncBrowserOpts)
            logging.getLogger(self.syncController.getLoggerName()).addHandler(self.lw)

            self.synchronizer = LinkedInBulkConnectionScraper(self.syncController, options, teardown_func=onComplete)
            self.syncController.connectionsScraped.connect(lambda: self.fetchValues(skipTemplates=True))

            QThreadPool.globalInstance().start(self.synchronizer)

            btn.setText('Stop')
        else:
            if self.synchronizer:
                try:
                    QThreadPool.globalInstance().cancel(self.synchronizer)
                except RuntimeError as e:
                    self.syncController.warning(str(e))
            onComplete()

    def scrapeConnectionsIndividually(self, checked):
        """Synchronizes account using options given in GUI"""

        btn = self.ui.scrapeIndividualConnectionsBtn
        originalText = btn.text()

        def onComplete():
            """Called on completion of the Synchronizer task"""

            btn.setChecked(False)
            if not self.syncController:
                return
            btn.setText('Closing...')
            btn.setEnabled(False)

            self.syncController.closing = True
            self.syncController.stop()

            del self.syncController
            del self.synchronizer

            self.synchronizer = None
            self.syncController = None

            btn.setText(originalText)
            btn.setEnabled(True)
            self.ui.scrapeBulkConnectionsBtn.setEnabled(True)
            self.ui.uploadConnectionsCSVBtn.setEnabled(True)
            self.ui.acceptConnectionRequestsBtn.setEnabled(True)
            self.ui.sendConnectionRequestsBtn.setEnabled(True)

        if checked:
            self.ui.scrapeBulkConnectionsBtn.setEnabled(False)
            self.ui.uploadConnectionsCSVBtn.setEnabled(False)
            self.ui.acceptConnectionRequestsBtn.setEnabled(False)
            self.ui.sendConnectionRequestsBtn.setEnabled(False)

            known = [(conn.name, conn.id) for conn in
                     Session.query(LinkedInConnection).filter(LinkedInConnection.account_id == self.account.id)]

            syncBrowserOpts = self.opts[:]
            if self.ui.headlessBoxGeneral.isChecked():
                syncBrowserOpts.append("headless")

            self.syncController = self.controllerConstructor(self.client.name, self.email, self.pwd,
                                                             browser=self.browser, options=syncBrowserOpts)

            logging.getLogger(self.syncController.getLoggerName()).addHandler(self.lw)

            self.synchronizer = LinkedInIndividualConnectionScraper(self.syncController, known, teardown_func=onComplete)

            QThreadPool.globalInstance().start(self.synchronizer)

            btn.setText('Stop')
        else:
            if self.synchronizer:
                try:
                    QThreadPool.globalInstance().cancel(self.synchronizer)
                except RuntimeError as e:
                    self.syncController.warning(str(e))
            onComplete()

    def acceptConnectionRequests(self, checked):
        """Synchronizes account using options given in GUI"""

        btn = self.ui.acceptConnectionRequestsBtn
        originalText = btn.text()

        def onComplete():
            """Called on completion of the Synchronizer task"""

            btn.setChecked(False)
            if not self.syncController:
                return
            btn.setText('Closing...')
            btn.setEnabled(False)

            self.syncController.closing = True
            self.syncController.stop()

            del self.syncController
            del self.synchronizer

            self.synchronizer = None
            self.syncController = None

            btn.setText(originalText)
            btn.setEnabled(True)
            self.ui.scrapeIndividualConnectionsBtn.setEnabled(True)
            self.ui.scrapeBulkConnectionsBtn.setEnabled(True)
            self.ui.uploadConnectionsCSVBtn.setEnabled(True)
            self.ui.sendConnectionRequestsBtn.setEnabled(True)

        if checked:
            self.ui.scrapeIndividualConnectionsBtn.setEnabled(False)
            self.ui.scrapeBulkConnectionsBtn.setEnabled(False)
            self.ui.uploadConnectionsCSVBtn.setEnabled(False)
            self.ui.sendConnectionRequestsBtn.setEnabled(False)

            syncBrowserOpts = self.opts[:]
            if self.ui.headlessBoxGeneral.isChecked():
                syncBrowserOpts.append("headless")

            self.syncController = self.controllerConstructor(self.client.name, self.email, self.pwd,
                                                             browser=self.browser, options=syncBrowserOpts)

            logging.getLogger(self.syncController.getLoggerName()).addHandler(self.lw)

            self.synchronizer = LinkedInConnectionRequestAccepter(self.syncController, teardown_func=onComplete)

            QThreadPool.globalInstance().start(self.synchronizer)

            btn.setText('Stop')
        else:
            if self.synchronizer:
                try:
                    QThreadPool.globalInstance().cancel(self.synchronizer)
                except RuntimeError as e:
                    self.syncController.warning(str(e))
            onComplete()

    def sendConnectionRequests(self, checked):
        """Synchronizes account using options given in GUI"""

        btn = self.ui.sendConnectionRequestsBtn
        originalText = btn.text()

        def onComplete():
            """Called on completion of the Synchronizer task"""

            btn.setChecked(False)
            if not self.syncController:
                return
            btn.setText('Closing...')
            btn.setEnabled(False)

            self.syncController.closing = True
            self.syncController.stop()

            del self.syncController
            del self.synchronizer

            self.synchronizer = None
            self.syncController = None

            btn.setText(originalText)
            btn.setEnabled(True)
            self.ui.scrapeIndividualConnectionsBtn.setEnabled(True)
            self.ui.scrapeBulkConnectionsBtn.setEnabled(True)
            self.ui.uploadConnectionsCSVBtn.setEnabled(True)
            self.ui.acceptConnectionRequestsBtn.setEnabled(True)

        if checked:
            self.ui.scrapeIndividualConnectionsBtn.setEnabled(False)
            self.ui.scrapeBulkConnectionsBtn.setEnabled(False)
            self.ui.uploadConnectionsCSVBtn.setEnabled(False)
            self.ui.acceptConnectionRequestsBtn.setEnabled(False)

            criteria = {}

            def setCriteria(crit):
                nonlocal criteria
                criteria = crit

            if maxRequests := self.account.getTodaysRemainingActions():
                scd = SearchCriteriaDialog(self, buttonText=' Send Requests ',
                                           maxRequests=maxRequests)
                scd.useCriteria.connect(setCriteria)
                ok = scd.exec_()
            else:
                ok = 0

            if ok:
                syncBrowserOpts = self.opts[:]
                if self.ui.headlessBoxGeneral.isChecked():
                    syncBrowserOpts.append("headless")

                self.syncController = self.controllerConstructor(self.client.name, self.email, self.pwd,
                                                                 browser=self.browser, options=syncBrowserOpts)

                logging.getLogger(self.syncController.getLoggerName()).addHandler(self.lw)

                self.synchronizer = LinkedInConnectionRequestSender(self.syncController, criteria, teardown_func=onComplete)

                QThreadPool.globalInstance().start(self.synchronizer)

                btn.setText('Stop')
            else:
                btn.setChecked(False)
                self.ui.scrapeIndividualConnectionsBtn.setEnabled(True)
                self.ui.scrapeBulkConnectionsBtn.setEnabled(True)
                self.ui.uploadConnectionsCSVBtn.setEnabled(True)
                self.ui.acceptConnectionRequestsBtn.setEnabled(True)
        else:
            if self.synchronizer:
                try:
                    QThreadPool.globalInstance().cancel(self.synchronizer)
                except RuntimeError as e:
                    self.syncController.warning(str(e))
            onComplete()
