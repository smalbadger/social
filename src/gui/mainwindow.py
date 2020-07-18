from PySide2.QtWidgets import QMainWindow
from PySide2.QtCore import Slot
from gui.ui.ui_mainwindow import Ui_MainWindow
from site_controllers.linkedin import LinkedInController


class SocialView(QMainWindow):

    CONTROLLERS = {
        'LinkedIn': LinkedInController
    }

    DEV_RECIPIENT = 'Samuel Badger'

    def __init__(self):

        QMainWindow.__init__(self)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Variables
        self.controller = None
        self.browser = None  # This will only be a string. Gets converted to object in controller.py

        # Connect signals
        self.ui.confirmButton.toggled.connect(self.confirmClicked)

    @Slot(bool)
    def confirmClicked(self, checked: bool):
        """
        Handles what happens when confirm button is clicked
        """

        if checked:

            fileIsOk = self.checkConnectionsFile()

            if fileIsOk:
                # Enable rest of GUI
                self.ui.loggingBox.setEnabled(True)
                self.ui.counterBox.setEnabled(True)
                self.ui.startButton.setEnabled(True)
                self.ui.stopButton.setEnabled(True)

                # Visually disable settings
                self.ui.platformDropdown.setDisabled(True)
                self.ui.browserDropdown.setDisabled(True)
                self.ui.templateNumber.setDisabled(True)
                self.ui.showBrowser.setDisabled(True)

                # Get info and instantiate controller
                platform = self.ui.platformDropdown.currentText()
                browser = self.ui.browserDropdown.currentText()
                connectionsFilePath = self.ui.connectionsFileEdit.text()
                if not self.ui.showBrowser.isChecked():
                    args = ['--headless']
                else:
                    args = []

                self.controller = SocialView.CONTROLLERS[platform](browser, connectionsFilePath, args)

                # Connect signals
                self.ui.startButton.clicked.connect(lambda: self.controller.sendMessageTo(SocialView.DEV_RECIPIENT))
                self.ui.stopButton.clicked.connect(lambda: self.controller.stop())

        else:
            self.ui.stopButton.click()

            # Disable rest of GUI
            self.ui.loggingBox.setEnabled(False)
            self.ui.counterBox.setEnabled(False)
            self.ui.startButton.setEnabled(False)
            self.ui.stopButton.setEnabled(False)

            # Re-enable settings
            self.ui.platformDropdown.setDisabled(False)
            self.ui.browserDropdown.setDisabled(False)
            self.ui.templateNumber.setDisabled(False)
            self.ui.showBrowser.setDisabled(False)

    def checkConnectionsFile(self) -> bool:
        """
        Checks if the entered connections file is valid. If not
        """

        # TODO
        return True
