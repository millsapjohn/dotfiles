from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QMainWindow
from enmapbox.testing import initQgisApplication
from enmapbox import EnMAPBox
import qgisresources.images

qgisresources.images.qInitResources()

qgsApp = initQgisApplication()
enmapBox = EnMAPBox(None)
enmapBox.run()
enmapBox.ui.hide()
layer = enmapBox.addSource(r'C:\source\QGISPlugIns\rastertimeseriesmanager\testdata\timeseries.bsq')

def test_RdpAxisWidget():
    from rasterdataplotting.gui.rdpaxiswidget import RdpAxisWidget
    ui = RdpAxisWidget()
    ui.setName('My Axis')
    ui.show()
    qgsApp.exec_()

def test_RdpScatterPlotWidget():
    from rasterdataplotting.gui.rdpscatterplotwidget import RdpScatterPlotWidget
    ui = RdpScatterPlotWidget()
    ui.show()
    qgsApp.exec_()

def test_RdpDockWidget():
    from rasterdataplotting.gui.rdpdockwidget import RdpDockWidget

    ui = QMainWindow()
    ui.addDockWidget(Qt.RightDockWidgetArea, RdpDockWidget())
    ui.show()
    qgsApp.exec_()

if __name__ == '__main__':
    #test_RdpAxisWidget()
    test_RdpScatterPlotWidget()
    #test_RdpDockWidget()
