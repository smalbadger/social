from PySide2.QtWidgets import QWidget
from gui.ui.ui_instancewidget import Ui_mainWidget
from site_controllers.linkedin import LinkedInController


class InstanceWidget(QWidget):

    CONTROLLERS = {
        'LinkedIn': LinkedInController
    }

    def __init__(self, clientName, platformName):
        QWidget.__init__(self)

        self.ui = Ui_mainWidget()
        self.ui.setupUi(self)

        self.clientName = clientName
        self.platformName = platformName

        # TODO: Get credentials for client from database using their name
        # self.controller = InstanceWidget.CONTROLLERS[platformName]()

        self.connectSignalsToFunctions()

    def connectSignalsToFunctions(self):
        """
        Connects all UI signals to functions
        """

        # TODO: Connect signals
