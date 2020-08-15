
from PySide2.QtWidgets import QApplication
from gui.releasedialog import ReleaseDialog

if __name__ == '__main__':
    app = QApplication()
    dialog = ReleaseDialog()
    dialog.show()
    app.exec_()
