from PySide2.QtWidgets import QDialog, QProgressDialog, QMessageBox
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

    def fillLocations(self):

        prog = QProgressDialog('Getting possible locations...', 'Hide', 0, 0)
        prog.setWindowTitle('Fetching location data...')
        prog.setModal(True)

        def populate(locs):
            loc = None
            for loc in locs:
                self.ui.location.addItem(loc[0])

            prog.close()

            if not loc:
                QMessageBox.warning(parent=self.parent())
                self.close()

        task = Task(lambda: session.query(LinkedInConnection.location)
                    .filter(LinkedInConnection.account_id == self.account.id)
                    .distinct())

        task.finished.connect(populate)
        QThreadPool.globalInstance().start(task)

        prog.exec_()

    def accept(self):
        self.filterAccepted.emit(self.ui.location.currentText(), self.ui.numMessages.value())
        QDialog.accept(self)
