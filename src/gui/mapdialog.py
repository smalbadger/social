from PySide2.QtWidgets import QDialog, QDialogButtonBox, QApplication, QCompleter, QMessageBox
from PySide2.QtCore import Signal

from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from matplotlib.pyplot import Circle

import requests
import cartopy.crs as crs
from geopy.distance import distance
from geopy.geocoders import Photon, Nominatim

from gui.ui.ui_mapdialog import Ui_Dialog

http = requests.Session()


class MapDialog(QDialog):

    foundLocations = Signal(list)

    def __init__(self, parent, locations: list):
        QDialog.__init__(self, parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.point = None
        self.radius = None
        self.circle = None
        self.maxRadius = 110
        self.mapwidget = None
        self.nameToPoint = {}
        self.background = None
        self.ax = None
        self.oldMiles = None
        self.movingSlider = False
        self.oldText = ''
        self.locDict = {}

        # Photon is made to handle realtime search, Nominatim bans you for it (speaking from experience)
        # Nominatim has much better reversing though
        self.locate = Photon().geocode
        self.reverse = Nominatim(user_agent='Social').reverse

        # Interaction variables
        self.dragging = False

        self.allLocations = locations
        self.loadMap()
        self.updateRadius(self.ui.radiusSlider.value())
        self.connectSignals()

        self.ui.errorLabel.hide()
        self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        self.ui.locationEdit.setFixedWidth(self.width() / 3)

    def updateRadius(self, sliderVal):
        self.radius = self.maxRadius**(sliderVal/100)

    def loadMap(self):
        """
        Creates the map and fetches location info, then populates map with location info
        """

        # Creating the map
        fig = Figure(figsize=(10, 2.25), frameon=False)
        self.mapwidget = FigureCanvas(fig)  # the widget we'll add to the dialog

        ax = fig.add_subplot(1, 1, 1, projection=crs.PlateCarree(), frame_on=False)  # adds the map
        self.ax = ax
        ax.stock_img()  # adds coloring to map
        ax.add_wms('http://vmap0.tiles.osgeo.org/wms/vmap0', ['basic'])  # Adds details
        for spine in ax.spines.values():  # Removes black axes borders
            spine.set_visible(False)
        ax.set_position([0, 0, 1, 1])  # Removes frame

        locs = self.allLocations

        # Counting how many people are in each area
        for loc in locs:
            name = loc  # loc is a (name, ) tuple, so we just get the name out of it from the 0th position
            if name in self.locDict.keys():
                self.locDict[name] += 1
            else:
                self.locDict[name] = 1

        # Add locations to map
        for loc, num in self.locDict.items():
            location = self.locate(loc, timeout=1000)
            lon, lat = location.longitude, location.latitude

            # Dot size grows with number of connections at that location.
            # Also, dots are translucent in order to see multiple close points better
            point = Circle((lon, lat), radius=1 + .2 * num, color='red', alpha=.75)

            self.nameToPoint[loc] = point
            self.ax.add_artist(point)

        self.ui.locationLayout.addWidget(self.mapwidget, 0, 1)

    def connectSignals(self):

        # Connecting slider to circle radius and radius box
        def sliderMoved(newVal):
            self.movingSlider = True
            self.mapwidget.restore_region(self.background)
            self.updateRadius(newVal)
            self.circle.radius = self.radius
            self.ax.draw_artist(self.point)
            self.ax.draw_artist(self.circle)
            self.mapwidget.blit(self.ax.bbox)

            self.updateMiles()
            self.movingSlider = False

        self.ui.radiusSlider.valueChanged.connect(sliderMoved)

        # Connecting radius spinbox to circle radius and slider
        def spinboxChanged(newVal):
            if self.oldMiles and not self.dragging and not self.movingSlider:
                self.radius = min(newVal/self.oldMiles * self.radius, self.maxRadius)
                self.oldMiles = newVal
                self.mapwidget.restore_region(self.background)
                self.circle.radius = self.radius
                self.ax.draw_artist(self.point)
                self.ax.draw_artist(self.circle)
                self.mapwidget.blit(self.ax.bbox)

        self.ui.radiusBox.valueChanged.connect(spinboxChanged)

        # Connecting edited text to a new location on map
        def locationEdited(newText):
            if len(newText) > 5 and newText != self.oldText[:-1]:
                r = http.get('http://photon.komoot.de/api',
                             params={'q': newText,
                                     'limit': 5},
                             headers={'user-agent': 'social'}
                             ).json()

                # ------ This part is for suggestion, but it doesn't work yet -------
                # s = []  # list of suggestions
                # for feature in r['features']:  # Only getting the first 5 suggestions, maximum
                #     props = feature['properties']
                #     city = props.get('city')
                #     state = props.get('state')
                #     country = props.get('country')
                #     stg = ''
                #     if city:
                #         stg += city + ', '
                #     if state:
                #         stg += state + ', '
                #     stg += country
                #     s.append(stg)

                # comp = QCompleter(s)
                # self.ui.locationEdit.setCompleter(comp)

                center = tuple(r['features'][0]['geometry']['coordinates'])

                if center:
                    self.ui.errorLabel.hide()
                    self.point.center = center
                    self.circle.center = center
                    self.mapwidget.restore_region(self.background)
                    self.ax.draw_artist(self.point)
                    self.ax.draw_artist(self.circle)
                    self.mapwidget.blit(self.ax.bbox)
                else:
                    self.ui.errorLabel.show()

            self.oldText = newText

        self.ui.locationEdit.textEdited.connect(locationEdited)

        # Connect signals in the map area
        self.setupInteractionSignals()

    def setupInteractionSignals(self):

        # Button pressed
        def onpress(event):
            if event.button == 1:  # a left click
                if not self.point:
                    self.background = self.mapwidget.copy_from_bbox(self.ax.bbox)
                    self.ui.radiusSlider.setEnabled(True)
                    self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
                    self.ui.radiusBox.setEnabled(True)
                    self.point = Circle((event.xdata, event.ydata), .5, color='#0381ab')
                    self.circle = Circle((event.xdata, event.ydata), self.radius, color='#05abe3', alpha=0.5)
                    self.ax.add_artist(self.circle)
                    self.ax.add_artist(self.point)

                    self.updateMiles()
                else:
                    self.mapwidget.restore_region(self.background)
                    self.circle.center = self.point.center = event.xdata, event.ydata

                self.dragging = True
                self.ax.draw_artist(self.point)
                self.ax.draw_artist(self.circle)
                self.mapwidget.blit(self.ax.bbox)

        # Mouse moved
        def onmove(event):
            if self.dragging:
                x = event.xdata if event.xdata else self.point.center[0]
                y = event.ydata if event.ydata else self.point.center[1]

                self.mapwidget.restore_region(self.background)
                self.circle.center = self.point.center = x, y
                self.ax.draw_artist(self.point)
                self.ax.draw_artist(self.circle)
                self.mapwidget.blit(self.ax.bbox)

                # We also want to recalculate the radius
                self.updateMiles()

        # Mouse released
        def onrelease(event):
            if event.button == 1:
                x = event.xdata if event.xdata else self.point.center[0]
                y = event.ydata if event.ydata else self.point.center[1]

                self.dragging = False
                self.mapwidget.restore_region(self.background)
                self.circle.center = self.point.center = x, y
                self.ax.draw_artist(self.point)
                self.ax.draw_artist(self.circle)
                self.mapwidget.blit(self.ax.bbox)

                self.updateMiles()

                # 10 zoom means city-level accuracy,
                # check https://nominatim.org/release-docs/latest/api/Reverse/#result-limitation
                try:
                    location = self.reverse(self.point.center[::-1], zoom=10, timeout=1000)
                    self.ui.locationEdit.setText(location.raw['display_name'])
                except TypeError:
                    pass

        self.mapwidget.mpl_connect('button_press_event', onpress)
        self.mapwidget.mpl_connect('button_release_event', onrelease)
        self.mapwidget.mpl_connect('motion_notify_event', onmove)

    def updateMiles(self):
        # Updates the miles within a radius. Changes depending on circle placement since the globe is a sphere

        center = (self.point.center[1], self.point.center[0])
        topedge = (self.point.center[1] + self.radius, self.point.center[0])
        botedge = (self.point.center[1] - self.radius, self.point.center[0])
        if topedge[0] < 90:
            dist = round(distance(center, topedge).miles)
        elif botedge[0] > -90:
            dist = round(distance(center, botedge).miles)
        else:
            dist = 7590
        self.ui.radiusBox.setValue(dist)
        self.oldMiles = dist

    def accept(self):
        # Get all points below the circle
        locations = []
        cc = self.circle.center

        for name, point in self.nameToPoint.items():
            pc = point.center

            # If point is within circle
            if (pc[0] - cc[0]) ** 2 + (pc[1] - cc[1]) ** 2 <= self.radius ** 2:
                locations.append(name)

        if not locations:
            QMessageBox.warning(self, 'No connections in area',
                                'No connections were found in the selected area.\nPlease select a valid area.')
            return

        totConns = 0
        for lc in locations:
            totConns += self.locDict[lc]
        locStr = self.reverse(self.point.center[::-1], zoom=10, timeout=1000).raw['display_name']

        info = {'name': f'{totConns} connections within {self.ui.radiusBox.value()} miles of {locStr}',
                'locations': locations}

        self.foundLocations.emit(info)
        QDialog.accept(self)


# if __name__ == '__main__':
#     app = QApplication()
#
#     win = MapDialog(None, ['Orange, California, United States of America', 'Berlin, Germany', 'Paris, France'])
#
#     win.show()
#     app.exec_()
