from PySide2.QtWidgets import QDialog, QDialogButtonBox, QProgressDialog
from PySide2.QtCore import Signal, QThreadPool

from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from matplotlib.pyplot import Circle

import cartopy.crs as crs
from geopy.geocoders import Nominatim

from gui.ui.ui_filterdialog import Ui_Dialog
from database.linkedin import session, LinkedInConnection
from common.threading import Task


class FilterDialog(QDialog):

    filterAccepted = Signal(list, int)

    def __init__(self, curAccount, parent):
        QDialog.__init__(self, parent=parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.point = None
        self.circle = None
        self.maxRadius = 110
        self.mapwidget = None
        self.radius = self.ui.radiusSlider.value() * self.maxRadius / 100
        self.nameToPoint = {}

        self.account = curAccount
        self.loadMap()
        self.connectSignals()

    def loadMap(self):
        """
        Creates the map and fetches location info, then populates map with location info
        """

        # Creating the map
        fig = Figure(figsize=(10, 2.25), frameon=False)
        self.mapwidget = FigureCanvas(fig)  # the widget we'll add to the dialog
        ax = fig.add_subplot(1, 1, 1, projection=crs.PlateCarree(), frame_on=False)  # adds the map
        ax.stock_img()  # adds coloring to map
        ax.add_wms('http://vmap0.tiles.osgeo.org/wms/vmap0', ['basic'])  # Adds details
        for spine in ax.spines.values():  # Removes black axes borders
            spine.set_visible(False)
        ax.set_position([0, 0, 1, 1])  # Removes frame

        # Tool to get lat and long from address or location
        locator = Nominatim(user_agent="social")

        #
        # Just for visual understanding, this is where the database is queried, then the next def is called
        #

        def continueLoading(locations):

            locs = list(locations)

            # Counting how many people are in each area
            locDict = {}
            for loc in locs:
                name = locDict.get(loc[0], None)
                if name:
                    locDict[name] += 1
                else:
                    locDict[loc[0]] = 1

            # Add locations to map
            for loc, num in locDict.items():
                location = locator.geocode(loc)
                lon, lat = location.longitude, location.latitude

                # Dot size grows with number of connections at that location.
                # Also, dots are translucent in order to see multiple close points better
                point = Circle((lon, lat), radius=1 + .2 * num, color='red', alpha=.75)

                self.nameToPoint[loc] = point
                ax.add_artist(point)

            def onclick(event):

                if event.button == 1:  # a left click
                    if not self.point:
                        self.ui.radiusSlider.setEnabled(True)
                        self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
                        self.point = ax.scatter(event.xdata, event.ydata, color='#0381ab')
                        self.circle = Circle((event.xdata, event.ydata), self.radius, color='#05abe3', alpha=0.5)
                        ax.add_artist(self.circle)
                    else:
                        self.point.remove()
                        self.point = ax.scatter(event.xdata, event.ydata, color='#0381ab')
                        self.circle.center = event.xdata, event.ydata

                    self.mapwidget.draw()

            self.mapwidget.mpl_connect('button_press_event', onclick)
            self.ui.locationLayout.addWidget(self.mapwidget, 0)

        prog = QProgressDialog('Getting possible locations and preparing map...', 'Hide', 0, 0, self.parent().window())
        prog.setWindowTitle('Fetching location data...')
        prog.setModal(True)

        # Query db for locations (note: NOT distinct)
        task = Task(lambda: session.query(LinkedInConnection.location)
                    .filter(LinkedInConnection.account_id == self.account.id))

        task.finished.connect(continueLoading)
        task.finished.connect(prog.close)

        QThreadPool.globalInstance().start(task)

        prog.exec_()

    def connectSignals(self):

        # Enabling/disabling associated field
        self.ui.useLocation.toggled.connect(self.ui.location.setEnabled)
        self.ui.useMaxMessages.toggled.connect(self.ui.numMessages.setEnabled)

        # Enabling/disabling ok button
        def slot(): self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(self.atLeastOneChecked())
        self.ui.useLocation.toggled.connect(slot)
        self.ui.useMaxMessages.toggled.connect(slot)

        slot()

        # Tying slider to circle radius
        def adapt(val):
            self.radius = val * self.maxRadius / 100
            self.circle.radius = self.radius
            self.mapwidget.draw()

        self.ui.radiusSlider.valueChanged.connect(adapt)

    def atLeastOneChecked(self):
        return (self.ui.useLocation.isChecked() and self.point) \
               or self.ui.useMaxMessages.isChecked()

    def accept(self):
        if self.ui.useLocation.isChecked() and self.point:
            # Get all points below the circle
            locations = []
            cc = self.circle.center

            for name, point in self.nameToPoint.items():
                pc = point.center

                # If point is within circle
                if (pc[0] - cc[0])**2 + (pc[1] - cc[1])**2 <= self.radius**2:
                    locations.append(name)

        else:
            locations = []

        if self.ui.useMaxMessages.isChecked():
            maxMessages = self.ui.numMessages.value()
        else:
            maxMessages = 10

        self.filterAccepted.emit(locations, maxMessages)

        QDialog.accept(self)
