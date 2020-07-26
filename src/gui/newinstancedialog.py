
from PySide2.QtWidgets import QDialog

from gui.ui.ui_newinstancedialog import Ui_Dialog

class NewInstanceDialog(QDialog):
    def __init__(self):
        super().__init__(None)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

    def getClient(self):
        return self.ui.clientBox.currentText()

    def getBrowser(self):
        return self.ui.browserBox.currentText()

    def getPlatform(self):
        return self.ui.platformBox.currentText()
