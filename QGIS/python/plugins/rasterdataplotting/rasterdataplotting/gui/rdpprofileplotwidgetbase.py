from os.path import join
import math
import numpy as np
from osgeo import gdal
from qgis.gui import *
from qgis.core import *
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *

from ..site import pyqtgraph as pg
from .. import ui
from .rdpprofilewidget import RdpProfileWidget
from ..site import rastertimeseriesmanager as rtm
from .rdpaxiswidget import RdpAxisWidget

debug = True


class RdpProfilePlotWidgetBase(QWidget):
    iface = None  # set by RdpDockWidget

    def axisMode(self):
        raise NotImplementedError()

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        uic.loadUi(join(ui.path, 'profileplotwidget.ui'), self)
        self.ui = _Ui(self)
        self._initUi()
        self.mapTool = QgsMapToolEmitPoint(canvas=self.mapCanvas())
        self.dataHandler = DataHandler(showPlot=self.ui.showPlot(),
            plotType=self.axisMode(),
            profiles=self.ui.profiles(),
            mapX=self.ui.mapX(), mapY=self.ui.mapY(),
            mapCanvas=self.mapCanvas(), mapTool=self.mapTool,
            modeAxisXIndices=self.ui.modeAxisXIndices(),
            modeAxisXWavelength=self.ui.modeAxisXWavelength(),
            showSymbol=self.ui.showSymbol(), symbol=self.ui.symbol(),
            symbolSize=self.ui.symbolSize(),
            showLine=self.ui.showLine(), lineSize=self.ui.lineSize(),
            plotWidget=self.ui.plotWidget())
        self._connectSignals()
        self.resetData()

    def _initUi(self):
        self.nprofiles = 10
        if self.axisMode() == RdpAxisWidget.Mode.SpectralProfile:
            self.ui.modeAxisXIndices().setText('Band Number')
            self.ui.modeAxisXWavelength().setText('Nanometers')
            self.ui.mapTool().setText('Select Spectral Profiles')
            self.ui.modeAxisXIndices().setChecked(True)
            self.ui.modeAxisXWavelength().setChecked(False)
        elif self.axisMode() == RdpAxisWidget.Mode.TemporalProfile:
            self.ui.modeAxisXIndices().setText('Date Number')
            self.ui.modeAxisXWavelength().setText('Decimal Years')
            self.ui.mapTool().setText('Select Temporal Profiles')
            self.ui.modeAxisXIndices().setChecked(False)
            self.ui.modeAxisXWavelength().setChecked(True)
        else:
            assert 0

        for i in range(self.nprofiles):
            self.ui.profile(i).ui.axis().initMode(mode=self.axisMode())
            self.ui.profile(i).ui.axis().setName('Profile {}'.format(i + 1))
        self._splitter.setSizes([1, 99999])

    def _connectSignals(self):

        self.ui.showPlot().toggled.connect(self.readAndPlotData)

        # map tool
        self.mapTool.canvasClicked.connect(self.onCanvasClicked)

        # location group
        self.ui.mapTool().clicked.connect(self.onMapToolClicked)

        # x axis group
        self.ui.modeAxisXIndices().toggled.connect(self.resetData)
        self.ui.modeAxisXWavelength().toggled.connect(self.resetData)

        # symbol group
        self.ui.showSymbol().toggled.connect(self.resetData)
        self.ui.symbol().currentIndexChanged.connect(self.resetData)
        self.ui.symbolSize().valueChanged.connect(self.resetData)

        # line group
        self.ui.showLine().toggled.connect(self.resetData)
        self.ui.lineSize().valueChanged.connect(self.resetData)

        # profiles
        for i in range(self.nprofiles):
            profile = self.ui.profile(i)
            profile.ui.axis().sigAxisChanged.connect(self.resetData)
            profile.ui.color().colorChanged.connect(self.resetData)
            profile.ui.show().toggled.connect(self.resetData)

        # link to raster timeseries manager
        if rtm.rtmInstalled:
            # Can't connect directly, because RTM plugin may be initialized later.
            for i in range(self.nprofiles):
                self.ui.profile(i).ui.axis().ui.updateDate().clicked.connect(self.onLayerUpdateDateClicked)

    def onLayerUpdateDateClicked(self):
        if rtm.rtmInterface(raiseError=False) is not None:
            # RTM plugin should be initialized now, so we can connect.
            rtm.rtmInterface().sigDateChanged.connect(self.onDateChanged)
            # Disconnect indirection.
            for i in range(self.nprofiles):
                self.ui.profile(i).ui.axis().ui.updateDate().clicked.disconnect(self.onLayerUpdateDateClicked)

    def onMapToolClicked(self):
        self.mapCanvas().setMapTool(self.mapTool)

    def onCanvasClicked(self, point, button):
        assert isinstance(point, QgsPointXY)
        if button == Qt.LeftButton:
            self.ui.mapX().setText(str(round(point.x(), 4)))
            self.ui.mapY().setText(str(round(point.y(), 4)))

            # if first raster is not selected, use the top most raster under the point
            if not isinstance(self.ui.profile(0).ui.axis().ui.layer().currentLayer(), QgsRasterLayer):
                for layer in self.mapCanvas().layers():
                    if isinstance(layer, QgsRasterLayer):
                        tr = QgsCoordinateTransform(self.mapCanvas().mapSettings().destinationCrs(),
                            layer.crs(), QgsProject.instance())
                        point2 = tr.transform(point)
                        if layer.extent().contains(point2):
                            self.ui.profile(0).ui.axis().ui.layer().setLayer(layer)
                            return

            self.readAndPlotData()

    def onDateChanged(self, date, snap):
        for i in range(self.nprofiles):
            profile = self.ui.profile(i)
            axis = profile.ui.axis()
            if axis.ui.updateDate().isChecked():
                axis.blockSignals(True)
                axis.ui.date().setDate(date=date, snap=snap)
                axis.blockSignals(False)
                self.readAndPlotData()

        if debug:
            print('date changed: {}'.format(date.toString('yyyy-MM-dd')))

    def mapCanvas(self):
        mapCanvas = self.iface.mapCanvas()
        assert isinstance(mapCanvas, QgsMapCanvas)
        return mapCanvas

    def resetData(self):
        self.readAndPlotData()

    def readAndPlotData(self):
        self.dataHandler.readAndPlot()


class DataHandler(object):

    def __init__(self, showPlot, plotType,
            mapX, mapY, profiles, mapCanvas, mapTool, plotWidget,
            modeAxisXWavelength, modeAxisXIndices,
            showSymbol, symbol, symbolSize,
            showLine, lineSize):
        assert isinstance(showPlot, QToolButton)
        assert isinstance(plotType, int)
        assert isinstance(profiles, list)
        assert isinstance(mapCanvas, QgsMapCanvas)
        assert isinstance(mapTool, QgsMapTool)
        assert isinstance(mapX, QLineEdit)
        assert isinstance(mapY, QLineEdit)
        assert isinstance(plotWidget, pg.PlotWidget)
        assert isinstance(modeAxisXWavelength, QRadioButton)
        assert isinstance(modeAxisXIndices, QRadioButton)
        assert isinstance(showSymbol, QToolButton)
        assert isinstance(symbol, QComboBox)
        assert isinstance(symbolSize, QSpinBox)
        assert isinstance(showLine, QToolButton)
        assert isinstance(lineSize, QSpinBox)

        self.showPlot = showPlot
        self.plotType = plotType
        self.profiles = profiles
        self.mapX = mapX
        self.mapY = mapY
        self.mapCanvas = mapCanvas
        self.modeAxisXWavelength = modeAxisXWavelength
        self.modeAxisXIndices = modeAxisXIndices
        self.showSymbol = showSymbol
        self.symbol = symbol
        self.symbolSize = symbolSize
        self.showLine = showLine
        self.lineSize = lineSize
        self.mapTool = mapTool
        self.plotWidget = plotWidget
        self._plotDataItems = [self.plotWidget.getPlotItem().plot([0]) for _ in profiles]
        self._cacheXvaluesNanometers = dict()
        self._cacheXvaluesDecimalYears = dict()
        self.plotWidget.getPlotItem().plot()

    def point(self):
        try:
            return QgsPointXY(float(self.mapX.text()), float(self.mapY.text()))
        except:
            return None

    def _wavelength(self, layer, modeRaster, modeTimeseries, timeseries=None):

        key = layer, modeRaster, modeTimeseries

        if not key in self._cacheXvaluesNanometers:
            if modeRaster:
                ds = gdal.Open(layer.source())
                wlu = ds.GetMetadataItem('wavelength_units', 'ENVI')
                wl = ds.GetMetadataItem('wavelength', 'ENVI')
                if wl is not None:
                    wl = [float(v) for v in wl.replace('{', '').replace('}', '').split(',')]
            elif modeTimeseries:
                assert isinstance(timeseries, rtm.RtmRasterTimeseries)
                wlu = 'nanometers'
                wl = timeseries.wavelength()
            else:
                assert 0

            if wl is None:
                xvalues = None
            else:
                if wlu is None:
                    xvalues = None
                else:
                    if wlu.lower() in ['nanometers']:
                        xvalues = wl
                    elif wlu.lower() in ['micrometers']:
                        xvalues = [v * 1000 for v in wl]
                    else:
                        xvalues = None

            self._cacheXvaluesNanometers[key] = xvalues

        xvalues = self._cacheXvaluesNanometers[key]
        return xvalues

    def _decimalYears(self, layer, timeseries):
        assert isinstance(timeseries, rtm.RtmRasterTimeseries)
        key = layer

        if not key in self._cacheXvaluesDecimalYears:
            self._cacheXvaluesDecimalYears[key] = timeseries.decimalYears()

        xvalues = self._cacheXvaluesDecimalYears[key]
        return xvalues

    def readAndPlot(self):

        pointMapCanvas = self.point()

        showNext = True
        for profile, plotDataItem in zip(self.profiles, self._plotDataItems):
            assert isinstance(profile, RdpProfileWidget)
            assert isinstance(plotDataItem, pg.PlotDataItem)

            layer = profile.ui.axis().ui.layer().currentLayer()
            if isinstance(layer, QgsRasterLayer) and pointMapCanvas is not None:

                provider = layer.dataProvider()
                assert isinstance(provider, QgsRasterDataProvider)
                extent = layer.extent()
                assert isinstance(extent, QgsRectangle)

                point = self.mapTool.toLayerCoordinates(layer, pointMapCanvas)

                xloc = math.floor((point.x() - extent.xMinimum()) / layer.rasterUnitsPerPixelX())
                yloc = math.floor((extent.yMaximum() - point.y()) / layer.rasterUnitsPerPixelY())
                if xloc < 0 or xloc >= layer.width():
                    xloc = -1
                if yloc < 0 or yloc >= layer.height():
                    yloc = -1

                # update pixel location
                for w, v in zip([profile.ui.axis().ui.x(), profile.ui.axis().ui.y()], [xloc, yloc]):
                    w.blockSignals(True)
                    w.setValue(v)
                    w.blockSignals(False)

                # read data (y values)
                try:
                    scale = float(profile.ui.scale().text())
                except:
                    scale = 1.

                if profile.ui.axis().ui.modeRaster().isChecked():
                    firstBand = 1
                    numberOfBands = layer.bandCount()
                elif profile.ui.axis().ui.modeTimeseries().isChecked():
                    timeseries = profile.ui.axis().ui.date().timeseries()
                    dateIndex = profile.ui.axis().ui.date().currentIndex()
                    firstBand = timeseries.numberOfBands() * dateIndex + 1
                    numberOfBands = timeseries.numberOfBands()
                else:
                    assert 0

                if self.plotType == RdpAxisWidget.Mode.SpectralProfile:
                    start = 0
                    end = numberOfBands
                    step = 1
                elif self.plotType == RdpAxisWidget.Mode.TemporalProfile:
                    start = profile.ui.axis().ui.name().currentIndex()
                    end = layer.bandCount()
                    step = profile.ui.axis().ui.date().timeseries().numberOfBands()
                else:
                    assert 0

                yvalues = [scale * provider.sample(point=point, band=firstBand + i)[0] for i in range(start, end, step)]

                # x values
                if self.plotType == RdpAxisWidget.Mode.SpectralProfile:

                    if self.modeAxisXIndices.isChecked():
                        xvalues = None
                    elif self.modeAxisXWavelength.isChecked():
                        xvalues = self._wavelength(layer=layer,
                            modeRaster=profile.ui.axis().ui.modeRaster().isChecked(),
                            modeTimeseries=profile.ui.axis().ui.modeTimeseries().isChecked(),
                            timeseries=profile.ui.axis().ui.date().timeseries())
                    else:
                        assert 0

                elif self.plotType == RdpAxisWidget.Mode.TemporalProfile:
                    xvalues = self._decimalYears(layer=layer, timeseries=profile.ui.axis().ui.date().timeseries())
                else:
                    assert 0

                # plot data
                plotDataItem.clear()
                if self.modeAxisXIndices.isChecked():
                    numbers = range(1, len(yvalues) + 1)
                    plotDataItem.setData(numbers, yvalues)
                elif self.modeAxisXWavelength.isChecked():
                    if xvalues is not None:
                        plotDataItem.setData(xvalues, yvalues)

                if not profile.ui.show().isChecked():
                    plotDataItem.clear()

                color = profile.ui.color().color()

                if profile.ui.show().isChecked() and self.showPlot.isChecked() and self.showLine.isChecked():
                    pen = QPen(QBrush(color), self.lineSize.value())
                    pen.setCosmetic(True)
                    plotDataItem.setPen(pen)
                else:
                    plotDataItem.setPen(None)

                if profile.ui.show().isChecked() and self.showPlot.isChecked() and self.showSymbol.isChecked():
                    symbols = list(reversed(['t', 't1', 't2', 't3', 's', 'p', 'h', 'star', '+', 'd', 'o']))
                    symbol = symbols[self.symbol.currentIndex()]

                    plotDataItem.setSymbol(symbol)
                    plotDataItem.setSymbolBrush(color)
                    plotDataItem.setSymbolPen(color)
                    plotDataItem.setSymbolSize(self.symbolSize.value())
                else:
                    plotDataItem.setSymbol(None)

                profile.setVisible(True)
                showNext = True
            else:
                plotDataItem.clear()
                profile.setVisible(showNext)
                showNext = False


class _Ui(object):

    def __init__(self, obj):
        self.obj = obj

    def plotWidget(self):
        assert isinstance(self.obj._plotWidget, pg.PlotWidget)
        return self.obj._plotWidget

    # location group
    def showPlot(self):
        assert isinstance(self.obj._showPlot, QToolButton)
        return self.obj._showPlot

    def mapX(self):
        assert isinstance(self.obj._mapX, QLineEdit)
        return self.obj._mapX

    def mapY(self):
        assert isinstance(self.obj._mapY, QLineEdit)
        return self.obj._mapY

    def mapTool(self):
        assert isinstance(self.obj._mapTool, QToolButton)
        return self.obj._mapTool

    # x axis group
    def modeAxisXWavelength(self):
        assert isinstance(self.obj._modeAxisXWavelength, QRadioButton)
        return self.obj._modeAxisXWavelength

    def modeAxisXIndices(self):
        assert isinstance(self.obj._modeAxisXIndices, QRadioButton)
        return self.obj._modeAxisXIndices

    # symbol group
    def showSymbol(self):
        assert isinstance(self.obj._showSymbol, QToolButton)
        return self.obj._showSymbol

    def symbol(self):
        assert isinstance(self.obj._symbol, QComboBox)
        return self.obj._symbol

    def symbolSize(self):
        assert isinstance(self.obj._symbolSize, QSpinBox)
        return self.obj._symbolSize

    # lines group
    def showLine(self):
        assert isinstance(self.obj._showLine, QToolButton)
        return self.obj._showLine

    def lineSize(self):
        assert isinstance(self.obj._lineSize, QSpinBox)
        return self.obj._lineSize

    # profiles
    def profiles(self):
        return [self.profile(i) for i in range(self.obj.nprofiles)]

    def profile(self, i):
        profile = getattr(self.obj, '_profile_{}'.format(i))
        assert isinstance(profile, RdpProfileWidget)
        return profile
