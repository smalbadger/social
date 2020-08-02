from PySide2.QtWidgets import QDialog, QMessageBox, QProgressDialog
from PySide2.QtCore import QThreadPool, Signal

from gui.ui.ui_newclientdialog import Ui_Dialog

from database.linkedin import session, Client, LinkedInAccount
from common.threading import Task


class NewClientDialog(QDialog):

    clientCreated = Signal(Client)

    def __init__(self):
        QDialog.__init__(self)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.tabWidget.setTabEnabled(1, False) # disable facebook (not implemented)
        self.ui.tabWidget.setTabEnabled(2, False) # disable instagram (not implemented)
        self.ui.tabWidget.setTabEnabled(3, False) # disable twitter (not implemented)

        self.ui.errorLabel.hide()

    def accept(self):

        self.ui.errorLabel.hide()

        clientName = self.ui.clientName.text()
        clientEmail = self.ui.clientEmail.text()
        clientPhone = self.ui.clientPhone.text()
        isTester = self.ui.testerBox.isChecked()
        self.client = Client(name=clientName, email=clientEmail, phone=clientPhone, tester=isTester)
        dbEntries = [self.client]

        accounts = 0
        errors = []

        if not clientName:
            QMessageBox.critical(self, 'Error', 'Please enter a client name.', QMessageBox.Ok)
            return

        u, e, p = self.ui.linkedInUsername.text(), self.ui.linkedInEmail.text(), self.ui.linkedInPassword.text()
        if u or e or p:
            if not u:
                errors.append("Need LinkedIn Username")
            elif not e:
                errors.append("Need LinkedIn Email")
            #TODO: Force password storage once we have the encryption down
            # elif not p:
            #     errors.append("Need LinkedIn Password")
            else:
                accounts += 1
                linkedinAccount = LinkedInAccount(email=e, username=u, password=p, tester=isTester)
                self.client.linkedin_account = linkedinAccount
                dbEntries.append(linkedinAccount)

        # TODO: Implement Facebook, Instagram, and LinkedIn as needed.

        if errors:
            self.ui.errorLabel.setText("\n".join(errors))
            self.ui.errorLabel.show()
            return

        if not accounts:
            response = QMessageBox.question(self, "Warning", "Are you sure you'd like to create a client with no accounts?", QMessageBox.Yes, QMessageBox.No)
            if response == QMessageBox.No:
                return

        prog = QProgressDialog("Creating new client. please wait...", "Hide", 0, 0, parent=self)
        prog.setModal(True)

        def addToDB():
            session.add_all(dbEntries)
            session.commit()
            self.clientCreated.emit(self.client)
            prog.close()

        task = Task(addToDB)
        task.finished.connect(prog.close)
        QThreadPool.globalInstance().start(task)
        prog.exec_()

        super().accept()
