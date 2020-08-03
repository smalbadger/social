from PySide2.QtWidgets import QDialog, QProgressDialog, QDialogButtonBox
from PySide2.QtCore import QThreadPool, Signal
from gui.ui.ui_filterdialog import Ui_Dialog
from common.threading import Task
from database.linkedin import session, LinkedInConnection


class FilterDialog(QDialog):

    filterAccepted = Signal(str, int)

    def __init__(self, curAccount, parent):
        QDialog.__init__(self, parent=parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.account = curAccount
        self.fillLocations()

        self.connectSignals()

    def fillLocations(self):

        prog = QProgressDialog('Getting possible locations...', 'Hide', 0, 0)
        prog.setWindowTitle('Fetching location data...')
        prog.setModal(True)

        def populate(locs):
            loc = None
            for loc in locs:
                self.ui.location.addItem(loc[0])

            prog.close()

        task = Task(lambda: session.query(LinkedInConnection.location)
                    .filter(LinkedInConnection.account_id == self.account.id)
                    .distinct())

        task.finished.connect(populate)
        QThreadPool.globalInstance().start(task)

        prog.exec_()

    def connectSignals(self):

        # Enabling/disabling associated field
        self.ui.useLocation.toggled.connect(self.ui.location.setEnabled)
        self.ui.useMaxMessages.toggled.connect(self.ui.numMessages.setEnabled)

        # Enabling/disabling ok button
        def slot(): self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(self.atLeastOneChecked())
        self.ui.useLocation.toggled.connect(slot)
        self.ui.useMaxMessages.toggled.connect(slot)

        slot()

    def atLeastOneChecked(self):
        return self.ui.useLocation.isChecked() \
               or self.ui.useMaxMessages.isChecked()

    def accept(self):
        if self.ui.useLocation.isChecked():
            location = self.ui.location.currentText()
        else:
            location = None

        if self.ui.useMaxMessages.isChecked():
            maxMessages = self.ui.numMessages.value()
        else:
            maxMessages = 10

        self.filterAccepted.emit(location, maxMessages)

        QDialog.accept(self)
