"""
Scrape the LinkedIn conversations
"""

import os
import sys
from PySide2.QtWidgets import QApplication

from gui.mainwindow import SocialView
import qtmodern.styles as styles

if __name__ == "__main__":

    # add the driver to the PATH variable
    os.environ["PATH"] += os.pathsep + os.path.abspath(os.path.join("..", "drivers", "windows"))
    os.environ["PATH"] += os.pathsep + os.path.abspath(os.path.join("drivers", "windows"))

    app = QApplication([])
    styles.darkClassic(app)

    view = SocialView()
    view.show()

    sys.exit(app.exec_())
