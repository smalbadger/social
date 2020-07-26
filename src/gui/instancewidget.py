from PySide2.QtWidgets import QWidget
from PySide2.QtCore import QThreadPool
from gui.ui.ui_instancewidget import Ui_mainWidget
from site_controllers.linkedin import LinkedInController, LinkedInMessenger

class InstanceWidget(QWidget):

    def __init__(self, username, email, password):
        super().__init__()

        self.ui = Ui_mainWidget()
        self.ui.setupUi(self)

        self.username = username
        self.email = email
        self.password = password
        self.messagingController = LinkedInController(username, email, password)
        self.messenger = None

        self.ui.startStopButton.clicked.connect(self.startStopMessaging)

    def startStopMessaging(self, start=True):
        """Starts or stops the messaging controller based on the status of the start/stop button."""

        # TODO: When I start, then stop the messenger manually, I get a bunch of HTTP errors. This probably needs to be
        #  fixed in the Controller class somehow so that we can safely stop at any point.

        startStopButton = self.ui.startStopButton

        def onComplete():
            self.messenger = None
            self.messagingController.stop()
            startStopButton.setText("Start")
            startStopButton.setChecked(False)

        if start:
            msg = "Hello"
            recipients = ["Mary-Ann Johnson", "Bobby Tables", "George d'tousla canil-bater"]
            self.messenger = LinkedInMessenger(self.messagingController, msg, recipients, teardown_func=onComplete)
            QThreadPool.globalInstance().start(self.messenger)
            startStopButton.setText("Stop")
        else:
            if self.messenger:
                QThreadPool.globalInstance().cancel(self.messenger)
            onComplete()
