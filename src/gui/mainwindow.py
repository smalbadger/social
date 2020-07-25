from PySide2.QtWidgets import QMainWindow
from PySide2.QtCore import Slot
from gui.ui.ui_mainwindow import Ui_MainWindow
from site_controllers.linkedin import LinkedInController


class SocialView(QMainWindow):

    CONTROLLERS = {
        'LinkedIn': LinkedInController
    }

    def __init__(self):

        QMainWindow.__init__(self)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.instances = []

        # Connect signals
        self.ui.newInstanceButton.clicked.connect(self.makeNewInstance)

    def makeNewInstance(self):
        """
        Opens a new instance dialog, and creates the instance if a copy isn't running
        """
