"""
Scrape the LinkedIn conversations
"""

import os
import sys
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QTimer

from gui.mainwindow import SocialView
import common.instance as inst
import qtmodern.styles as styles


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

    t = QTimer(view)
    t.timeout.connect(inst.checkRun)
    t.start(10000)  # Every 10 seconds

    sys.exit(app.exec_())
