import os
from semantic_version import Version
from PySide2.QtWidgets import QDialog, QButtonGroup, QDialogButtonBox

from gui.ui.ui_releasedialog import Ui_Dialog
from common.version import getCurrentVersion, setVersion, setChangeLog, getCommitMessagesSince, addVersionTagToLastCommit


class ReleaseDialog(QDialog):

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.typeGroup = QButtonGroup(self)
        self.typeGroup.setExclusive(True)
        self.typeGroup.addButton(self.ui.majorReleaseButton)
        self.typeGroup.addButton(self.ui.minorReleaseButton)
        self.typeGroup.addButton(self.ui.patchButton)
        self.typeGroup.buttonClicked.connect(self.updateTargetRelease)

        self.current_version = getCurrentVersion()
        self.target_version = self.current_version
        self.ui.currentVersionLabel.setText(str(self.current_version))
        self.updateTargetRelease()

        self.suggestChangeLog()

    def suggestChangeLog(self):
        repoDir = os.path.join('..', '.git')
        commitMessages = getCommitMessagesSince(repoDir, self.current_version)
        separator = '-'*50 + '\n'
        self.ui.changeLogEdit.setPlainText(separator.join(commitMessages))

    def updateTargetRelease(self):
        if self.ui.majorReleaseButton.isChecked():
            tv = self.current_version.next_major()
        elif self.ui.minorReleaseButton.isChecked():
            tv = self.current_version.next_minor()
        elif self.ui.patchButton.isChecked():
            tv = self.current_version.next_patch()
        else:
            tv = self.current_version

        self.target_version = tv
        self.ui.targetVersionLabel.setText(str(self.target_version))

        if self.current_version == self.target_version:
            enable = False
        else:
            enable = True

        self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enable)

    def accept(self):
        setVersion(self.target_version)
        addVersionTagToLastCommit(os.path.join('..', '.git'), self.target_version, f"Release v{self.target_version}")
        setChangeLog(self.ui.changeLogEdit.toPlainText())

        super().accept()
