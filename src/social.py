"""
Scrape the LinkedIn conversations
"""
import os
import sys
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QTimer


sys.path.append(os.path.abspath("./gui/rc/"))

from gui.mainwindow import SocialView
import common.instance as inst
import qtmodern.styles as styles

#     qApp.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

if __name__ == "__main__":
    # add the driver to the PATH variable
    os.environ["PATH"] += os.pathsep + os.path.abspath(os.path.join("..", "drivers", "windows"))

    app = QApplication([])
    styles.darkClassic(app)

    view = SocialView()
    view.show()

    inst.View = view

    t = QTimer(view)
    t.timeout.connect(inst.checkRun)
    t.start(10000)  # Every 10 seconds

    sys.exit(app.exec_())
