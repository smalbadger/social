"""
Scrape the LinkedIn conversations
"""
import os
import sys
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QPalette, QColor, Qt

sys.path.append(os.path.abspath("./gui/rc/"))

from gui.mainwindow import SocialView
import qtmodern.styles as styles


# def stylize(qApp):
#     qApp.setStyle("Fusion")
#
#     dark_palette = QPalette()
#     dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
#     dark_palette.setColor(QPalette.WindowText, Qt.white)
#     dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
#     dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
#     dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
#     dark_palette.setColor(QPalette.ToolTipText, Qt.white)
#     dark_palette.setColor(QPalette.Text, Qt.white)
#     dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
#     dark_palette.setColor(QPalette.ButtonText, Qt.white)
#     dark_palette.setColor(QPalette.BrightText, Qt.red)
#     dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
#     dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
#     dark_palette.setColor(QPalette.HighlightedText, Qt.black)
#     dark_palette.setColor(QPalette.Disabled, QPalette.Text, Qt.darkGray)
#     dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.darkGray)
#     qApp.setPalette(dark_palette)
#     qApp.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

if __name__ == "__main__":
    # add the driver to the PATH variable
    os.environ["PATH"] += os.pathsep + os.path.abspath(os.path.join("..", "drivers", "windows"))

    app = QApplication([])
    styles.darkClassic(app)

    view = SocialView()
    view.show()

    sys.exit(app.exec_())
