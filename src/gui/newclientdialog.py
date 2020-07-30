from gui.ui.ui_newclientdialog import Ui_Dialog
from PySide2.QtWidgets import QDialog, QMessageBox


class NewClientDialog(QDialog):

    def __init__(self):
        QDialog.__init__(self)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

    def accept(self):
        clientName = self.ui.clientName.text()
        noCredentials = True

        if not clientName:
            QMessageBox.warning(self, 'Error', 'Please enter a client name.', QMessageBox.Ok)
            return

        linkedIn = {
            'username': self.ui.linkedInUsername.text(),
            'password': self.ui.linkedInPassword.text()
        }
        facebook = {
            'username': self.ui.facebookUsername.text(),
            'password': self.ui.facebookPassword.text()
        }
        insta = {
            'username': self.ui.instaUsername.text(),
            'password': self.ui.instaPassword.text()
        }
        twitter = {
            'username': self.ui.twitterUsername.text(),
            'password': self.ui.twitterPassword.text()
        }

        if linkedIn['username'] and linkedIn['password']:
            noCredentials = False

