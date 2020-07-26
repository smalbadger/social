from PySide2.QtWidgets import QMainWindow
from gui.ui.ui_mainwindow import Ui_MainWindow
from gui.newinstancedialog import NewInstanceDialog
from gui.instancewidget import InstanceWidget


class SocialView(QMainWindow):

    def __init__(self):

        QMainWindow.__init__(self)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.instances = []

        # Connect signals
        self.ui.newInstanceButton.clicked.connect(self.openNID)

    def openNID(self):
        """
        Opens a new instance dialog
        """

        diag = NewInstanceDialog(parent=self)
        diag.setModal(True)
        diag.newInstanceCreated.connect(self.addInstance)
        diag.exec_()

    def addInstance(self, instance: InstanceWidget):
        """
        Handles adding a new instance

        :param instance: the new instance to add
        :type instance: InstanceWidget
        """

        # TODO: Placeholder, waiting for branches to merge
        pass
