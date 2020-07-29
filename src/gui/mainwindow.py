import logging

from PySide2.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QProgressDialog

from gui.ui.ui_mainwindow import Ui_MainWindow
from gui.instancetabwidget import InstanceTabWidget
from gui.newinstancedialog import NewInstanceDialog
from gui.instancewidget import InstanceWidget
from gui.logwidget import LogWidget

from common.nongui import RunInNewThread

from database.linkedin import session, Client


class SocialView(QMainWindow):

    def __init__(self):

        QMainWindow.__init__(self)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Setup the controller tab scroll area
        self.instanceTabWidget = QWidget()
        self.ui.tabScrollArea.setWidget(self.instanceTabWidget)
        self.instanceTabLayout = QVBoxLayout()
        self.instanceTabWidget.setLayout(self.instanceTabLayout)
        self.instanceTabLayout.addStretch()

        # Setup general log
        lw = LogWidget(self.ui.generalLogTextEdit)
        lw.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        lw.setLevel(logging.DEBUG)
        logging.getLogger("controller").addHandler(lw)

        # Variables
        self.controller = None
        self.browser = None  # This will only be a string. Gets converted to object in controller.py
        self.instances = {}

        # Other objects
        self.prog = QProgressDialog("Fetching clients, please wait...", "Hide", 0, 0, parent=self)
        self.prog.setModal(True)
        self.prog.hide()

        # Connect signals
        self.ui.newInstanceButton.clicked.connect(self.newInstanceClicked)

    def newInstanceClicked(self):
        """
        Opens a spinning animation while client list is being fetched, then opens a new instance dialog
        """
        self.prog.show()
        RunInNewThread(self.getClients).andConnect(self.openNID)

    def openNID(self, clients: list):
        """
        Opens a new instance dialog, populating it with clients list
        """
        self.prog.hide()

        nid = NewInstanceDialog(clients, parent=self)
        nid.setModal(True)
        nid.newInstanceCreated.connect(self.addInstance)
        nid.exec_()

    def addInstance(self, instance: InstanceWidget):
        """
        Handles adding a new instance

        :param instance: the new instance to add
        :type instance: InstanceWidget
        """

        newTab = InstanceTabWidget(instance.client, instance.platformName)
        self.instances[newTab] = instance

        newTab.clicked.connect(lambda: self.selectInstance(newTab))
        self.instanceTabLayout.insertWidget(0, newTab)

        self.selectInstance(newTab)

    def selectInstance(self, instanceTab):
        """Opens an instance by selecting an existing tab."""

        instanceWidget = self.instances.get(instanceTab)
        # This should never be None now that instancewidgets and instancetabs are made in pairs

        layout = self.ui.instanceBox.layout()
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i).widget()
            if item:
                item.setParent(None)

        layout.addWidget(instanceWidget)
        self.ui.instanceBox.setTitle(instanceTab.getName())

    #############################
    # Database stuff
    #############################
    def getClients(self) -> list:
        return session.query(Client).all()
