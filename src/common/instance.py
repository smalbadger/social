from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QThreadPool
from database.credentials import file_host, file_port, file_password, file_username
from ftplib import FTP
from common.threading import Task

ftp = FTP()
ftp.connect(host=file_host, port=file_port)
ftp.login(user=file_username, passwd=file_password)

View = None
Lock = False  # This allows the currently running function to finish before the app is forcefully exited
Waiting = False


# To check if social is allowed to be running, we use the following

def checkRun():
    global Waiting
    global Lock
    global View
    firstLine = True

    if not Waiting:
        def handler(valid):
            global Waiting
            nonlocal firstLine

            if firstLine:
                firstLine = False
                if valid in ('True', 'True\r\n'):
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

        ftp.retrlines('RETR social.txt', callback=handler)


def canRun():
    global Waiting
    firstLine = True
    result = False

    def handler(valid):
        global Waiting
        nonlocal firstLine
        nonlocal result

        if firstLine:
            firstLine = False

            if valid in ('True', 'True\r\n'):
                result = True
            else:
                result = False

            Waiting = False

    Waiting = True
    
    ftp.retrlines('RETR social.txt', callback=handler)

    while Waiting:
        pass

    return result
