from PySide2.QtWidgets import QWidget
from gui.ui.ui_instancewidget import Ui_mainWidget

class InstanceWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.ui = Ui_mainWidget()
        self.ui.setupUi(self)