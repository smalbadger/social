from PySide2.QtWidgets import QWidget, QApplication
from PySide2.QtGui import QPixmap
from PySide2.QtCore import Signal, QObject
from gui.ui.ui_controllertab import Ui_Form


class ControllerTab(QWidget):

    clicked = Signal()

    def __init__(self, username, platform):
        super().__init__(None)

        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.nameLabel.setText(username)
        self.ui.platformLabel.setText(platform)

        if platform == "LinkedIn":
            logoFile = u":/icon/resources/logos/linkedin.png"

        self.ui.logoLabel.setPixmap(QPixmap(logoFile))

    def mousePressEvent(self, ev):
        self.clicked.emit()