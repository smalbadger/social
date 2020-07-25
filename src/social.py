"""
Scrape the LinkedIn conversations
"""
import os
import sys
from PySide2.QtWidgets import QApplication

sys.path.append(os.path.abspath("./gui/rc/"))

from gui.mainwindow import SocialView

if __name__ == "__main__":
    # print(message)
    # print(LEVELS)
    # exit()

    # add the driver to the PATH variable
    os.environ["PATH"] += os.pathsep + os.path.abspath(os.path.join("..", "drivers", "windows"))

    app = QApplication([])

    view = SocialView()
    view.show()

    sys.exit(app.exec_())
