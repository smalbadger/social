from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QThreadPool
from common.threading import Task


View = None
Lock = False  # This allows the currently running function to finish before the app is forcefully exited
Waiting = False


# To check if social is allowed to be running, we use the following

def checkRun():
    global Waiting
    global Lock
    global View

    if not Waiting:
        with open('local-social.txt', 'r') as f:
            valid = f.readlines()[0]

        if valid in ('True', 'True\n'):
            return
        else:
            def waitForCurrentFunctionToFinish():
                while Lock:
                    pass

            def closeApp():
                QThreadPool.globalInstance().clear()
                View.closeAllBrowsers()
                QApplication.instance().quit()

            Waiting = True
            t = Task(waitForCurrentFunctionToFinish)
            t.finished.connect(closeApp)
            QThreadPool.globalInstance().start(t)