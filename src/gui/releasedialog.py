import os
import subprocess
import database.general
from ftplib import FTP
from PySide2.QtWidgets import QDialog, QButtonGroup, QDialogButtonBox, QProgressDialog
from PySide2.QtCore import QThreadPool

from gui.ui.ui_releasedialog import Ui_Dialog
from database.credentials import file_host, file_port, file_password, file_username
from database.linkedin import LinkedInAccount

from common.threading import Task
from common.version import *

versionFile = os.path.abspath('version.txt')
changeLogFile = os.path.abspath('changelog.txt')

def uploadInstaller(v: Version):
    ftp = FTP()
    ftp.connect(host=file_host, port=file_port)
    ftp.login(user=file_username, passwd=file_password)

    localFile = f'../dist/social_installer_v{str(v)}.exe'
    remoteFile = f'installers/social_v{str(v)}.exe'
    with open(localFile, 'rb') as f:
        ftp.storbinary(f'STOR {remoteFile}', f)
    ftp.quit()

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
        self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        setVersion(self.target_version)

        try:
            print("Building the installer")
            prog = QProgressDialog("Building Installer", "Hide", 0, 0, self)
            prog.show()
            def build_installer():
                os.chdir('../scripts')
                subprocess.check_call(['python', 'build_installer.py'])
                os.chdir('../src/')
            t1 = Task(build_installer)
            t1.finished.connect(prog.close)
            QThreadPool.globalInstance().start(t1)
            prog.exec_()

            print("Uploading the installer")
            prog = QProgressDialog("Uploading Installer", "Hide", 0, 0, self)
            prog.show()
            t2 = Task(lambda: uploadInstaller(self.target_version))
            t2.finished.connect(prog.close)
            QThreadPool.globalInstance().start(t2)
            prog.exec_()

            print(f"Tagging the current commit with v{str(self.target_version)}")
            addVersionTagToLastCommit(os.path.join('..', '.git'), self.target_version, f"Release v{self.target_version}")

            print("Adding version record to the database")
            # Set all other versions to not active.
            for version in database.general.Session.query(database.general.Version).all():
                version.active = None
            # Create new active version.
            v = database.general.Version(semantic_id=str(self.target_version), change_log=self.ui.changeLogEdit.toPlainText(), active=True)
            database.general.Session.add(v)
            database.general.Session.commit()

        except Exception as e:
            print(f"Rolling back to {self.current_version}")
            setVersion(self.current_version)
            raise e

        finally:
            self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

        super().accept()