from PySide2.QtWidgets import QDialog
from PySide2.QtCore import Qt
from semantic_version import Version


from gui.ui.ui_updateversion import Ui_Dialog


class UpdateVersionDialog(QDialog):

    def __init__(self, version, parent=None):
        QDialog.__init__(self, parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.newVersionHeaderLabel.setText(f"Good News! Version {version.semantic_id} is available.")
        self.ui.changeLogSummaryEdit.setText(version.change_log)

        self.setWindowFlag(Qt.WindowCloseButtonHint, False)