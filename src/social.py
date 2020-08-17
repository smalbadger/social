"""
Scrape the LinkedIn conversations
"""

import os
import sys
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QTimer, QThreadPool

from gui.mainwindow import SocialView
import common.authenticate as inst
import qtmodern.styles as styles
from common.threading import Task
from common.version import update


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
        t = Task(update)
        QThreadPool.globalinstance().start(t)

    updateTimer = QTimer(view)
    securityTimer.timeout.connect(update)
    securityTimer.start(1_000) # Every minute

    sys.exit(app.exec_())
