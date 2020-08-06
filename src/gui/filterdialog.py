from PySide2.QtWidgets import QDialog, QDialogButtonBox, QProgressDialog
from PySide2.QtCore import Signal, QThreadPool
from database.linkedin import session, LinkedInConnection
from common.threading import Task

from gui.ui.ui_filterdialog import Ui_Dialog
from gui.mapdialog import MapDialog


class FilterDialog(QDialog):

    filterAccepted = Signal(tuple, tuple)

    def __init__(self, curAccount, parent):
        QDialog.__init__(self, parent=parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.allLocsDict = {}
        self.account = curAccount
        self.connectSignals()

    def connectSignals(self):

        # Enabling/disabling associated field
        self.ui.useLocation.toggled.connect(self.ui.location.setEnabled)
        self.ui.useLocation.toggled.connect(self.ui.addLFButton.setEnabled)
        self.ui.useMaxMessages.toggled.connect(self.ui.numMessages.setEnabled)

        # Enabling/disabling ok button
        def slot(): self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(self.atLeastOneChecked())
        self.ui.useLocation.toggled.connect(slot)
        self.ui.useMaxMessages.toggled.connect(slot)

        slot()

        self.ui.addLFButton.clicked.connect(self.newMapDialog)
        self.ui.locationsList.itemClicked.connect(lambda: self.ui.deleteLFButton.setEnabled(True))
        # self.ui.locationsList.itemClicked.connect(lambda: self.ui.deleteLFButton.setEnabled(True))
        self.ui.deleteLFButton.clicked.connect(self.removeCurrentLocEntry)

    def newMapDialog(self):

        prog = QProgressDialog('Opening map, please wait...', 'Hide', 0, 0, parent=self.window())
        prog.setModal(True)
        prog.setWindowTitle('Loading...')

        def openDialog(locations):
            md = MapDialog(self, [item[0] for item in list(locations)])
            md.foundLocations.connect(self.addLocEntry)
            prog.close()
            md.exec_()

        task = Task(lambda: session.query(LinkedInConnection.location)
                    .filter(LinkedInConnection.account_id == self.account.id))
        prog.show()

        task.finished.connect(openDialog)
        QThreadPool.globalInstance().start(task)

        prog.exec_()

    def addLocEntry(self, info):
        name = info['name']
        locs = info['locations']

        self.ui.locationsList.addItem(name)
        self.allLocsDict[name] = locs

    def removeCurrentLocEntry(self):

        itm = self.ui.locationsList.currentItem()
        txt = itm.text()
        idx = self.ui.locationsList.row(itm)
        self.ui.locationsList.takeItem(idx)
        self.allLocsDict.pop(txt)

        if self.ui.locationsList.count() == 0:
            self.ui.deleteLFButton.setEnabled(False)

    def atLeastOneChecked(self):
        return self.ui.useLocation.isChecked() or self.ui.useMaxMessages.isChecked()

    def accept(self):
        lists = [
            self.allLocsDict[self.ui.locationsList.itemAt(i, 0).text()] for i in range(self.ui.locationsList.count())
        ]
        locs = list(set().union(*lists))

        if self.ui.useMaxMessages.isChecked():
            maxMessages = self.ui.numMessages.value()
        else:
            maxMessages = 10

        # Making the tuples
        locations = (self.ui.useLocation.isChecked(), locs)
        maxMessages = (self.ui.useMaxMessages.isChecked(), maxMessages)

        self.filterAccepted.emit(locations, maxMessages)

        QDialog.accept(self)
