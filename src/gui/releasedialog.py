import os
import subprocess
import database.general
from subprocess import call
from database.credentials import file_host, file_port, file_password, file_username
from ftplib import FTP
from PySide2.QtWidgets import QDialog, QButtonGroup, QDialogButtonBox, QProgressDialog
from PySide2.QtCore import QThreadPool

from gui.ui.ui_releasedialog import Ui_Dialog

from common.threading import Task
from common.version import *

versionFile = os.path.abspath('version.txt')
changeLogFile = os.path.abspath('changelog.txt')

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

        # Check to make sure everything is committed
        status = subprocess.check_output(['git', 'status'])
        if b'nothing to commit, working tree clean' in status:
            self.ui.warningLabel.hide()
        else:
            self.ui.warningLabel.show()
            self.ui.warningLabel.setText("WARNING: Detected uncommitted changes. Please commit all files and resart this program.")

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
        changeLog = self.ui.changeLogEdit.toPlainText()

        v = database.general.Version(semantic_id=str(self.target_version), change_log=changeLog, active=True)
        database.general.Session.add(v)
        database.general.Session.commit()

        def build_installer():
            os.chdir('../scripts')
            call(['python', '-v', str(self.target_version), 'build_installer.py'])
            os.chdir('../src/')

        prog = QProgressDialog("Building Installer", "Hide", 0, 0, self)
        prog.show()
        t1 = Task(build_installer)
        t1.finished.connect(prog.close)
        QThreadPool.globalInstance().start(t1)
        prog.exec_()

        ftp = FTP()
        ftp.connect(host=file_host, port=file_port)
        ftp.login(user=file_username, passwd=file_password)

        localFile = f'../social_installer_v{str(self.target_version)}.exe'
        remoteFile = f'installers/social_v{str(self.target_version)}.exe'
        with open(localFile, 'r') as f:
            ftp.storbinary(f'STOR {remoteFile}', f)
        ftp.quit()

        super().accept()
