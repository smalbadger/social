"""
Scrape the LinkedIn conversations
"""

import os
import sys
import logging
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QTimer, QThreadPool, Signal, Qt

from gui.mainwindow import SocialView
import common.authenticate as inst
import qtmodern.styles as styles
from common.threading import Task
from common.version import downloadInstaller, triggerUpdate, updateInProgress, getCurrentVersion
from common.beacon import Beacon

logger = logging.getLogger("root")

if __name__ == "__main__":
    if not inst.canRun():
        exit(0)

    logging.info(f"Version: v{str(getCurrentVersion())}")

    # add the driver to the PATH variable
    os.environ["PATH"] += os.pathsep + os.path.abspath(os.path.join("..", "drivers", "windows"))
    os.environ["PATH"] += os.pathsep + os.path.abspath(os.path.join("drivers", "windows"))

    app = QApplication([])
    styles.darkClassic(app)
    size = app.desktop().size()

    view = SocialView()
    view.showMaximized()

    inst.View = view

    securityTimer = QTimer(view)
    securityTimer.timeout.connect(inst.checkRun)
    securityTimer.start(10_000)  # Every 10 seconds

    def updateSocial():
        if not updateInProgress:
            t = Task(downloadInstaller)
            t.finished.connect(triggerUpdate, type=Qt.BlockingQueuedConnection)
            QThreadPool.globalInstance().start(t)


    if not sys.executable.endswith("python.exe"):
        updateTimer = QTimer(view)
        updateTimer.timeout.connect(updateSocial)
        updateTimer.start(60_000)  # Every 1 minute

        initialUpdateTimer = QTimer(view)
        initialUpdateTimer.timeout.connect(updateSocial)
        initialUpdateTimer.setSingleShot(True)
        initialUpdateTimer.start(1_000)  # trigger after 1 second

    sys.exit(app.exec_())
