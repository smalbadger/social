from PySide2.QtWidgets import QWidget, QApplication
from PySide2.QtGui import QPixmap, QColor
from PySide2.QtCore import Signal, QObject, QTimer, QThreadPool
from gui.ui.ui_instancetabwidget import Ui_Form
from database.linkedin import LinkedInAccountDailyActivity

from common.threading import Task


class InstanceTabWidget(QWidget):

    clicked = Signal()

    def __init__(self, client, platform):
        super().__init__(None)

        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.client = client
        self.ui.nameLabel.setText(client.name)
        self.ui.platformLabel.setText(platform)

        if platform == "LinkedIn":
            logoFile = u":/icon/resources/logos/linkedin.png"

        scrnProp = QApplication.desktop().height() / 2160
        self.ui.logoLabel.setPixmap(QPixmap(logoFile).scaled(80 * scrnProp, 80 * scrnProp))

        self.updateActivityInfo()

    def updateActivityInfo(self):

        def getColor(val):
            val = 100 - val*100
            hue = val * 1.2
            color = QColor()
            color.setHsl(hue, 255, 127)
            return f"rgb({color.red()}, {color.green()}, {color.blue()});"

        def update(todayRecord):
            usedActions = todayRecord.message_count + todayRecord.connection_request_count
            actionLimit = todayRecord.activity_limit

            if usedActions < actionLimit:
                styleSheet = f"QLabel {{color: {getColor(usedActions/actionLimit)}}}"
            else:
                styleSheet = "QLabel {color: rgb(255, 0, 0); background-color: rgb(0,0,0);}"

            self.ui.usedActions.setText(str(usedActions))
            self.ui.usedActions.setStyleSheet(styleSheet)
            self.ui.activityLimit.setText(str(actionLimit))

        task = Task(lambda: LinkedInAccountDailyActivity.getToday(self.client.linkedin_account.id))
        task.finished.connect(update)
        QThreadPool.globalInstance().start(task)

    def getName(self):
        return self.ui.nameLabel.text()

    def mousePressEvent(self, ev):
        self.clicked.emit()
