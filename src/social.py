"""
Scrape the LinkedIn conversations
"""

import os
import sys
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QTimer, QThreadPool, Signal, Qt

from gui.mainwindow import SocialView
import common.authenticate as inst
import qtmodern.styles as styles
from common.threading import Task
from common.version import downloadInstaller, triggerUpdate, updateInProgress
from common.beacon import Beacon


if __name__ == "__main__":
    if not inst.canRun():
        exit(0)

    # add the driver to the PATH variable
    os.environ["PATH"] += os.pathsep + os.path.abspath(os.path.join("..", "drivers", "windows"))
    os.environ["PATH"] += os.pathsep + os.path.abspath(os.path.join("drivers", "windows"))

    app = QApplication([])
    styles.darkClassic(app)

    view = SocialView()
    view.show()

    inst.View = view

    securityTimer = QTimer(view)
    securityTimer.timeout.connect(inst.checkRun)
    securityTimer.start(10_000)  # Every 10 seconds

    def updateSocial():
        if not updateInProgress:
            t = Task(downloadInstaller)
            t.finished.connect(triggerUpdate, type=Qt.BlockingQueuedConnection)
            QThreadPool.globalInstance().start(t)

    updateTimer = QTimer(view)
    securityTimer.timeout.connect(updateSocial)
    securityTimer.setSingleShot(True)
    securityTimer.start(5_000) # Every 10 minutes

    sys.exit(app.exec_())
