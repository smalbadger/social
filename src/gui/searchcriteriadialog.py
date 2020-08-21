from PySide2.QtWidgets import QDialog, QDialogButtonBox
from PySide2.QtCore import Signal, Qt
from gui.ui.ui_searchcriteriadialog import Ui_Dialog


class SearchCriteriaDialog(QDialog):

    useCriteria = Signal(dict)

    def __init__(self, parent, buttonText: str = 'Search', maxRequests=200):
        QDialog.__init__(self, parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # This is the dictionary that will be returned
        self.criteria = {
            '2nd Connections': self.ui.secondConnections.isChecked(),
            '3rd Connections': self.ui.thirdConnections.isChecked(),
            'Locations': [],
            'Companies': [],
            'First Name': '',
            'Last Name': '',
            'Request Limit': 1
        }

        self.boxSS = self.ui.companyBox.styleSheet()

        self.ui.buttonBox.button(QDialogButtonBox.Ok).setText(buttonText)
        self.ui.maxRequestsBox.setMaximum(maxRequests)

        self.blockEnter = False
        # Writing to the lineedits requires pressing enter, but the focusing is horrible and decides to close the
        #  window at the same time. I did everything to try getting around this with Qt's methods; nothing worked.

        self.connectSignals()

    def connectSignals(self):
        """
        Connects all signals to functions
        """

        crit = self.criteria
        two = self.ui.secondConnections
        thr = self.ui.thirdConnections

        # 2nd connections button
        def twoToggled(chk):
            if not chk and thr.isEnabled():
                thr.setChecked(True)
                crit['2nd Connections'] = chk
            else:
                two.setChecked(True)
                crit['2nd Connections'] = True

        two.toggled.connect(twoToggled)

        # 3rd connections button
        def thrToggled(chk):
            if not chk:
                two.setChecked(True)
            crit['3rd Connections'] = chk

        thr.toggled.connect(thrToggled)

        # Location bar
        def addLocation():
            self.blockEnter = True
            loc = (box := self.ui.locationBox).text()

            if loc not in (lst := crit['Locations']) + ['']:
                box.setStyleSheet(self.boxSS)
                self.ui.locationList.addItem(loc)
                box.clear()
                lst.append(loc)
            else:
                box.setStyleSheet("border: 1px solid red")

        self.ui.locationBox.returnPressed.connect(addLocation)

        # Location list
        def removeLocation(loc):
            ind = self.ui.locationList.row(loc)
            self.ui.locationList.takeItem(ind)
            crit['Locations'].remove(loc.text())

        self.ui.locationList.itemDoubleClicked.connect(removeLocation)

        # Company bar
        def addCompany():
            self.blockEnter = True
            comp = (box := self.ui.companyBox).text()

            if comp not in (lst := crit['Companies']) + ['']:
                box.setStyleSheet(self.boxSS)
                self.ui.companyList.addItem(comp)
                box.clear()
                lst.append(comp)
            else:
                box.setStyleSheet("border: 1px solid red")

        self.ui.companyBox.returnPressed.connect(addCompany)

        # Company list
        def removeCompany(comp):
            ind = self.ui.companyList.row(comp)
            self.ui.companyList.takeItem(ind)
            crit['Companies'].remove(comp.text())

        self.ui.companyList.itemDoubleClicked.connect(removeCompany)

    def accept(self):
        """
        Emits the criteria dictionary
        """

        if not self.blockEnter:
            self.criteria['Last Name'] = self.ui.lastNameBox.text()
            self.criteria['First Name'] = self.ui.firstNameBox.text()
            self.criteria['Request Limit'] = self.ui.maxRequestsBox.value()

            self.useCriteria.emit(self.criteria)

            QDialog.accept(self)
        else:
            self.blockEnter = False

    def close(self):
        """
        Only here to handle focus issues
        """
        if not self.blockEnter:
            QDialog.close(self)
        else:
            self.blockEnter = False

