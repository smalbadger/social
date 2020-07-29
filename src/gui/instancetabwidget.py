from PySide2.QtWidgets import QWidget, QApplication
from PySide2.QtGui import QPixmap
from PySide2.QtCore import Signal, QObject
from gui.ui.ui_instancetabwidget import Ui_Form


class InstanceTabWidget(QWidget):

    clicked = Signal()

    def __init__(self, username, platform):
        super().__init__(None)

        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.nameLabel.setText(username)
        self.ui.platformLabel.setText(platform)

        if platform == "LinkedIn":
            logoFile = u":/icon/resources/logos/linkedin.png"

        scrnProp = QApplication.desktop().height() / 2160
        self.ui.logoLabel.setPixmap(QPixmap(logoFile).scaled(80 * scrnProp, 80 * scrnProp))

    def getName(self):
        return self.ui.nameLabel.text()

    def mousePressEvent(self, ev):
        self.clicked.emit()
