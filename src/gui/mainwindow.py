from PySide2.QtWidgets import QMainWindow, QWidget, QVBoxLayout

from gui.ui.ui_mainwindow import Ui_MainWindow
from gui.instancetabwidget import InstanceTabWidget
from gui.newinstancedialog import NewInstanceDialog
from gui.instancewidget import InstanceWidget


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

        # Variables
        self.controller = None
        self.browser = None  # This will only be a string. Gets converted to object in controller.py
        self.instances = {}

        # Connect signals
        self.ui.newInstanceButton.clicked.connect(self.openNID)

    def openNID(self):
        """
        Opens a new instance dialog
        """

        nid = NewInstanceDialog(parent=self)
        nid.setModal(True)
        nid.newInstanceCreated.connect(self.addInstance)
        nid.exec_()

    def addInstance(self, instance: InstanceWidget):
        """
        Handles adding a new instance

        :param instance: the new instance to add
        :type instance: InstanceWidget
        """

        newTab = InstanceTabWidget(instance.clientName, instance.platformName)
        self.instances[newTab] = instance

        newTab.clicked.connect(lambda: self.selectInstance(newTab))
        self.instanceTabLayout.insertWidget(0, newTab)

        self.selectInstance(newTab)

    def selectInstance(self, instanceTab):
        """Opens an instance by selecting an existing tab."""

        instanceWidget = self.instances.get(instanceTab, None)

        layout = self.ui.instanceBox.layout()
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i).widget()
            if item:
                item.setParent(None)

        layout.addWidget(instanceWidget)
        self.ui.instanceBox.setTitle(instanceTab.getName())
