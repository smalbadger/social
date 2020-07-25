from PySide2.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PySide2.QtCore import Slot

from gui.ui.ui_mainwindow import Ui_MainWindow
from gui.controllertab import ControllerTab
from site_controllers.linkedin import LinkedInController


class SocialView(QMainWindow):

    CONTROLLERS = {
        'LinkedIn': LinkedInController
    }

    def __init__(self):

        QMainWindow.__init__(self)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Setup the controller tab scroll area
        self.controllerTabWidget = QWidget()
        self.ui.tabScrollArea.setWidget(self.controllerTabWidget)
        self.controllerTabLayout = QVBoxLayout()
        self.controllerTabWidget.setLayout(self.controllerTabLayout)

        # Variables
        self.controller = None
        self.browser = None  # This will only be a string. Gets converted to object in controller.py
        self.instances = []

        # Connect signals
        self.ui.newInstanceButton.clicked.connect(self.makeNewInstance)

    def makeNewInstance(self):
        """
        Opens a new instance dialog, and creates the instance if a copy isn't running
        """
