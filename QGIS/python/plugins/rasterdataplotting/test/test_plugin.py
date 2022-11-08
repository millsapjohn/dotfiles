from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
from qgis.gui import *
from qgis.core import *

from enmapbox.testing import initQgisApplication
from enmapbox import EnMAPBox

try:
    import qgisresources.images
    qgisresources.images.qInitResources()
except:
    pass

# start application and open test dataset
qgsApp = initQgisApplication()
#enmapBox = EnMAPBox(None)
#enmapBox.run()
#enmapBox.ui.hide()

#from rasterdataplotting.rasterdataplotting.site import pyqtgraph as pg
#pg.setConfigOption('background', 'w')
#pg.setConfigOption('foreground', 'k')

testRaster = True
testTimeseries = not testRaster

if testRaster:
#    layer = QgsRasterLayer(r'C:\Work\data\jan_knorn\Sitzung_7\Daten\LC81930232015276.bsq', baseName='LC81930232015276')
#    layer2 = QgsRasterLayer(r'C:\source\QGISPlugIns\rastertimeseriesmanager\testdata\timeseries.bsq', baseName='timeseries')
    layer = QgsRasterLayer(r'C:\source\QGISPlugIns\enmap-box\enmapboxtestdata\enmap_berlin.bsq', baseName='enmap_berlin')
#    layer = QgsRasterLayer(r'\\141.20.140.222\endor\south-africa\level4\X0007_Y0007\2015-2017_001-365_HL_TSA_SEN2L_EVI_TSI.tif', baseName='force_debug')


#    roi = QgsVectorLayer(r'C:\Work\data\jan_knorn\Sitzung_7\Daten\roi.gpkg', baseName='roi')
    roi = None
    layers = [layer]

if testTimeseries:
    layer = QgsRasterLayer(r'C:\Work\data\FORCE\philippe\BGW\tc_bgw.vrt',
                           baseName='tc_bgw')
    roi = None
    layers = [layer]

QgsProject.instance().addMapLayers(layers)

class TestInterface(QgisInterface):

    def __init__(self):
        QgisInterface.__init__(self)

        self.ui = QMainWindow()
        self.ui.setWindowTitle('QGIS')
        self.ui.setWindowIcon(QIcon(r'C:\source\QGIS3-master\images\icons\qgis_icon.svg'))
        self.ui.resize(QSize(1500, 750))
        self.ui.canvas = QgsMapCanvas()
        self.ui.setCentralWidget(self.ui.canvas)
        self.ui.show()
        self.ui.canvas.setLayers([roi, layer])
        self.ui.canvas.setDestinationCrs(layer.crs())
        self.ui.canvas.setExtent(layer.extent())

    def addDockWidget(self, area, dockwidget):
        self.ui.addDockWidget(area, dockwidget)

    def mapCanvas(self):
        assert isinstance(self.ui.canvas, QgsMapCanvas)
        return self.ui.canvas


def test_RdpPlugin():
    from rasterdataplotting.rasterdataplotting.plugin import RdpPlugin

    iface = TestInterface()

    rdpPlugin = RdpPlugin(iface=iface)
    rdpPlugin.initGui()

    iface.mapCanvas().destinationCrsChanged.emit()
    iface.mapCanvas().layersChanged.emit()

    if testTimeseries:
        from rastertimeseriesmanager.rastertimeseriesmanager.plugin import RtmPlugin
        rtmPlugin = RtmPlugin(iface=iface)
        rtmPlugin.initGui()
        rtmPlugin.rtmInterface.ui.layer().setCurrentIndex(0)

    scatterPlot = rdpPlugin.rdpInterface.ui.ui.scatterPlot()
    scatterPlot.ui.axisX().ui.layer().setCurrentIndex(1)
    scatterPlot.ui.axisY().ui.layer().setCurrentIndex(1)
    scatterPlot.ui.axisX().ui.band().setLayer(layer)
    scatterPlot.ui.axisY().ui.band().setLayer(layer)

    if testRaster:
        scatterPlot.ui.axisX().ui.band().setCurrentIndex(2)
        scatterPlot.ui.axisY().ui.band().setCurrentIndex(3)

    if testTimeseries:
        scatterPlot.ui.axisX().ui.date().setLayer(layer)
        scatterPlot.ui.axisX().ui.name().setLayer(layer)
        scatterPlot.ui.axisY().ui.date().setLayer(layer)
        scatterPlot.ui.axisY().ui.name().setLayer(layer)

        scatterPlot.ui.axisX().ui.band().setCurrentIndex(0)
        scatterPlot.ui.axisX().ui.date().setCurrentIndex(0)
        scatterPlot.ui.axisX().ui.name().setCurrentIndex(1)

        scatterPlot.ui.axisY().ui.band().setCurrentIndex(1)
        scatterPlot.ui.axisY().ui.date().setCurrentIndex(0)
        scatterPlot.ui.axisY().ui.name().setCurrentIndex(2)

        scatterPlot.ui.axisX().ui.updateBins().setChecked(False)
        scatterPlot.ui.axisY().ui.updateBins().setChecked(False)
        scatterPlot.ui.axisX().ui.bins().setValue(255)
        scatterPlot.ui.axisY().ui.bins().setValue(255)

    if roi is not None:
        scatterPlot.ui.layerRoi().setLayer(roi)

    qgsApp.exec_()

if __name__ == '__main__':
    test_RdpPlugin()
