"""
Scrape the LinkedIn conversations
"""

print("Hello world")

import os
print("1")
import sys
print("2")
from PySide2.QtWidgets import QApplication
print("3")
# Necessary to make cx-freeze get the appropriate dependencies
import sqlalchemy.sql.default_comparator
print("4")
sys.path.append(os.path.abspath("./gui/rc/"))
print("5")
from gui.mainwindow import SocialView
print("6")
import qtmodern.styles as styles
print("7")
print("__MAIN__:",__name__)

if __name__ == "__main__":


    # add the driver to the PATH variable
    os.environ["PATH"] += os.pathsep + os.path.abspath(os.path.join("..", "drivers", "windows"))

    app = QApplication([])
    styles.darkClassic(app)

    view = SocialView()
    view.show()

    sys.exit(app.exec_())
