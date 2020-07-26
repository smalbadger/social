from PySide2.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QDialog
from PySide2.QtCore import Slot

from gui.ui.ui_mainwindow import Ui_MainWindow
from gui.instancetabwidget import InstanceTabWidget
from gui.newinstancedialog import NewInstanceDialog
from gui.instancewidget import InstanceWidget
from site_controllers.linkedin import LinkedInController


class SocialView(QMainWindow):

    CONTROLLERS = {
        'LinkedIn': LinkedInController
    }

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
        self.ui.newInstanceButton.clicked.connect(self.makeNewInstance)

    def makeNewInstance(self):
        """
        Opens a new instance dialog, and creates the instance if a copy isn't running
        """
        nid = NewInstanceDialog()
        nid.exec_()

        if nid.result() == QDialog.Accepted:
            newTab = InstanceTabWidget(nid.getClient(), nid.getPlatform())
            newTab.clicked.connect(lambda: self.selectInstance(newTab))
            self.instanceTabLayout.insertWidget(0, newTab)
            self.selectInstance(newTab)

    def selectInstance(self, instanceTab):
        """Opens an instance by selecting an existing tab."""
        print("Selected")
        instanceWidget = self.instances.get(instanceTab, None)
        if not instanceWidget:
            instanceWidget = InstanceWidget()
            self.instances[instanceTab] = instanceWidget

        layout = self.ui.instanceBox.layout()
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i).widget()
            if item:
                item.setParent(None)

        layout.addWidget(instanceWidget)
        self.ui.instanceBox.setTitle(instanceTab.getName())