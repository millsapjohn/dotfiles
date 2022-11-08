import traceback
import builtins
from os.path import join, dirname
import math
import numpy as np
from scipy.stats import binned_statistic_2d, pearsonr
from scipy.optimize import curve_fit
from osgeo import gdal, ogr, osr
from qgis.gui import *
from qgis.core import *
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *

from ..site import pyqtgraph as pg
from .. import rdputils
from .. import ui
from .rdpaxiswidget import RdpAxisWidget
from .rdpscatterplotimageviewwidget import RdpScatterPlotImageViewWidget
from ..site import rastertimeseriesmanager as rtm


debug = not True

class RdpScatterPlotWidget(QWidget):

    iface = None # set by RdpDockWidget

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        uic.loadUi(join(ui.path, 'scatterplotwidget.ui'), self)
        self.ui = _Ui(self)
        self._initUi()

        self.dataReaderX = DataReader(
            axis=self.ui.axisX(), mapCanvas=self.mapCanvas(),
            modeDataExtentWholeRaster=self.ui.modeDataExtentWholeRaster(),
            modeDataExtentMapCanvas=self.ui.modeDataExtentMapCanvas(),
            referenceLayer=self.ui.axisX().ui.layer())
        self.dataReaderY = DataReader(
            axis=self.ui.axisY(), mapCanvas=self.mapCanvas(),
            modeDataExtentWholeRaster=self.ui.modeDataExtentWholeRaster(),
            modeDataExtentMapCanvas=self.ui.modeDataExtentMapCanvas(),
            referenceLayer=self.ui.axisX().ui.layer())
        self.dataReaderRoi = DataReaderRoi(
            layer=self.ui.layerRoi(), mapCanvas=self.mapCanvas(),
            modeDataExtentWholeRaster=self.ui.modeDataExtentWholeRaster(),
            modeDataExtentMapCanvas=self.ui.modeDataExtentMapCanvas(),
            referenceLayer=self.ui.axisX().ui.layer())
        self.dataBinner = DataBinner(readerX=self.dataReaderX, readerY=self.dataReaderY, readerRoi=self.dataReaderRoi)
        self.dataFitter = DataFitter(
            show=self.ui.showCurveFit(),
            binner=self.dataBinner, curveFitFunction=self.ui.curveFitFunction(),
            modeCurveFitAll=self.ui.modeCurveFitAll(), modeCurveFitRoi=self.ui.modeCurveFitRoi())
        self.dataPlotter = DataPlotter(
            binner=self.dataBinner, fitter=self.dataFitter, imageView=self.ui.imageView(),
            colorRampAll=self.ui.densityColorRampAll(), colorRampRoi=self.ui.densityColorRampRoi(),
            colorAll=self.ui.scatterColorAll(), colorRoi=self.ui.scatterColorRoi(),
            oneToOneColor=self.ui.oneToOneColor(),
            curveFitColor=self.ui.curveFitColor(), curveFitLabel=self.ui.curveFitSolution())
        self.dataOverlayer = DataOverlayer(
            show=self.ui.showSpectralRoi(), binner=self.dataBinner, color=self.ui.roiColor(),
            opacity=self.ui.roiOpacity(), mapCanvas=self.mapCanvas(), imageView=self.ui.imageView())
        self._mapCanvas = QgsMapCanvas()

        self._connectSignals()

    def _initUi(self):
        self.ui.axisX().setName('X Axis')
        self.ui.axisY().setName('Y Axis')
        self.ui.axisX().initMode(mode=self.ui.axisX().Mode.Band)
        self.ui.axisY().initMode(mode=self.ui.axisY().Mode.Band)

        # set default color ramp
        colorRamp = QgsStyle().defaultStyle().colorRamp('Spectral')
        colorRamp.invert()
        self.ui.densityColorRampAll().setColorRamp(colorRamp)
        self.ui.densityColorRampRoi().setColorRamp(colorRamp)

        self.ui.styledReapplyRoi().hide() # todo, not yet implemented

    def _connectSignals(self):
        # axes
        self.ui.axisX().sigAxisChanged.connect(self.readData)
        self.ui.axisY().sigAxisChanged.connect(self.readData)

        # image view
        self.ui.imageView().sigRangeChanged.connect(self.onRangeChanged)

        # data extent group
        self.ui.modeDataExtentMapCanvas().toggled.connect(lambda checked: self.ui.showSpectralRoi().setEnabled(checked))
        self.ui.modeDataExtentWholeRaster().toggled.connect(self.resetData)
        self.ui.modeDataExtentMapCanvas().toggled.connect(self.resetData)

        # all data group
        self.ui.showAll().clicked.connect(self.plotData)
        self.ui.modeDensityAll().toggled.connect(self.plotData)
        self.ui.modeScatterAll().toggled.connect(self.plotData)
        self.ui.densityStretchAll().valueChanged.connect(self.plotData)
        self.ui.scatterColorAll().colorChanged.connect(self.plotData)
        self.ui.densityColorRampAll().colorRampChanged.connect(self.plotData)

        # roi data group
        self.ui.showRoi().clicked.connect(self.plotData)
        self.ui.modeDensityRoi().toggled.connect(self.plotData)
        self.ui.modeScatterRoi().toggled.connect(self.plotData)
        self.ui.densityStretchRoi().valueChanged.connect(self.plotData)
        self.ui.layerRoi().layerChanged.connect(self.readData)
        self.ui.scatterColorRoi().colorChanged.connect(self.plotData)
        self.ui.densityColorRampRoi().colorRampChanged.connect(self.plotData)

        # roi data group
        #self.ui.showRoi().clicked.connect(self.plotData)
        self.ui.roiCircle().clicked.connect(self.onRoiCreated)
        self.ui.roiRectangle().clicked.connect(self.onRoiCreated)
        self.ui.roiPolygon().clicked.connect(self.onRoiCreated)
        self.ui.roiOpacity().valueChanged.connect(self.mapCanvas().refresh)
        self.ui.showSpectralRoi().toggled.connect(self.mapCanvas().refresh)

        # curve fitting group
        self.ui.showCurveFit().clicked.connect(self.onShowCurveFitClicked)
        self.ui.curveFitColor().colorChanged.connect(self.plotData)
        self.ui.curveFitFunction().currentIndexChanged.connect(self.processData)
        self.ui.modeCurveFitAll().toggled.connect(self.plotData)
        self.ui.modeCurveFitRoi().toggled.connect(self.plotData)

        # 1:1 line group
        self.ui.showOneToOne().clicked.connect(self.plotData)
        self.ui.oneToOneColor().colorChanged.connect(self.plotData)

        # map canvas
        self.mapCanvas().renderComplete.connect(self.onMapCanvasRenderComplete)

        # link to raster timeseries manager
        if rtm.rtmInstalled:
            # Can't connect directly, because RTM plugin may be initialized later.
            self.ui.axisX().ui.updateDate().clicked.connect(self.onAxisUpdateDateClicked)
            self.ui.axisY().ui.updateDate().clicked.connect(self.onAxisUpdateDateClicked)

    def onAxisUpdateDateClicked(self):
        if rtm.rtmInterface(raiseError=False) is not None:
            # RTM plugin should be initialized now, so we can connect.
            rtm.rtmInterface().sigDateChanged.connect(self.onDateChanged)
            # Disconnect indirection.
            self.ui.axisX().ui.updateDate().clicked.disconnect(self.onAxisUpdateDateClicked)
            self.ui.axisY().ui.updateDate().clicked.disconnect(self.onAxisUpdateDateClicked)

    def onShowCurveFitClicked(self):
        if self.dataFitter.isValid():
            self.plotData()
        else:
            self.processData()

    def onDateChanged(self, date, snap):
        assert isinstance(date, QDate)
        update = False
        for axis in (self.ui.axisX(), self.ui.axisY()):
            if axis.ui.updateDate().isChecked():
                axis.blockSignals(True)
                axis.ui.date().setDate(date=date, snap=snap)
                axis.blockSignals(False)
                update = True
        if update:
            if debug:
                print('date changed: {}'.format(date.toString('yyyy-MM-dd')))
            self.readData()

    def onMapCanvasRenderComplete(self, painter):
        if self.ui.showPlot().isChecked():
            if debug: print('onMapCanvasRenderComplete')
            self.readData()
            self.overlayData(painter=painter)

    def onRangeChanged(self, range):
        if debug: print('onRangeChanged')
        if self.dataReaderY.isValid() and self.dataReaderY.isValid():
            self.ui.axisX().ui.updateRange().setChecked(False)
            self.ui.axisY().ui.updateRange().setChecked(False)
            self.setRange(range)
            self.processData()

    def onRoiCreated(self):
        if self.sender() == self.ui.roiCircle():
            self.dataOverlayer.createCircle()
        elif self.sender() == self.ui.roiRectangle():
            self.dataOverlayer.createRectangle()
        elif self.sender() == self.ui.roiPolygon():
            self.dataOverlayer.createPolygon()

    def mapCanvas(self):
        mapCanvas = self.iface.mapCanvas()
        assert isinstance(mapCanvas, QgsMapCanvas)
        return mapCanvas

    def resetData(self):
        self.dataReaderX.setInvalidAndClearCache()
        self.dataReaderY.setInvalidAndClearCache()
        self.dataReaderRoi.setInvalidAndClearCache()
        self.dataBinner.setInvalidAndClearCache()
        self.dataFitter.setInvalidAndClearCache()
        self.dataOverlayer.setInvalidAndClearCache()
        self.mapCanvas().refresh()

    def readData(self):
        if self.ui.showPlot().isChecked():
            self.dataReaderX.read()
            self.dataReaderY.read()
            self.dataReaderRoi.read()
            self.processData()

    def processData(self):
        if self.ui.showPlot().isChecked():
            if self.dataReaderX.isValid() and self.dataReaderY.isValid():
                bins = self.bins()
                self.setBins(bins=bins)

                range = self.range()
                self.setRange(range=range)

                self.dataBinner.bin(bins=bins, range=range)
                self.dataFitter.fitPredict()
            else:
                self.dataBinner.setInvalidAndClearCache()
                self.dataFitter.setInvalidAndClearCache()
            self.plotData()

    def plotData(self):
        if self.ui.showPlot().isChecked():
            if self.dataBinner.isValid():
                range = self.range()
                self.dataPlotter.plotImage(range=range,
                                           stretchAll=self.stretchAll(),
                                           showAll=self.ui.showAll().isChecked(),
                                           showAllDensity=self.ui.modeDensityAll().isChecked(),
                                           showAllScatter=self.ui.modeScatterAll().isChecked(),
                                           stretchRoi=self.stretchRoi(),
                                           showRoi=self.ui.showRoi().isChecked(),
                                           showRoiDensity=self.ui.modeDensityRoi().isChecked(),
                                           showRoiScatter=self.ui.modeScatterRoi().isChecked(),
                                           showRoiStyled = self.ui.modeStyledRoi().isChecked())

                self.dataPlotter.plotFittedCurve(show=self.ui.showCurveFit().isChecked())
                self.dataPlotter.plotOneToOne(show=self.ui.showOneToOne().isChecked())

                self.dataPlotter.setRange(range=range)
            else:
                self.dataPlotter.clearImage()
                self.dataPlotter.clearFittedCurve()

    def overlayData(self, painter):
        if self.ui.showPlot().isChecked():
            self.dataOverlayer.overlay(painter=painter)

    def stretchAll(self):
        max = self.dataBinner.stretchAll(self.ui.densityStretchAll().value())
        return 1, max

    def stretchRoi(self):
        max = self.dataBinner.stretchRoi(self.ui.densityStretchRoi().value())
        return 1, max

    def bins(self):
        resX, resY = self.ui.imageView().getImageItem().pixelSize()
        sizeX, sizeY = self.ui.imageView().getImageItem().width(), self.ui.imageView().getImageItem().height()
        binsX = self.ui.axisX().bins(resX, sizeX)
        binsY = self.ui.axisY().bins(resY, sizeY)
        return binsX, binsY

    def setBins(self, bins):
        binsX, binsY = bins
        self.ui.axisX().setBin(bins=binsX)
        self.ui.axisY().setBin(bins=binsY)

    def range(self):
        rangeX = self.ui.axisX().range(dataRange=self.dataReaderX.range())
        rangeY = self.ui.axisY().range(dataRange=self.dataReaderY.range())
        return rangeX, rangeY

    def setRange(self, range):
        rangeX, rangeY = range
        self.ui.axisX().setRange(range=rangeX)
        self.ui.axisY().setRange(range=rangeY)

class DataHandlerBase(object):

    def setValid(self):
        self._isValid = True

    def setInvalidAndClearCache(self):
        self._isValid = False
        self.clearCache()

    def isValid(self):
        if hasattr(self, '_isValid'):
            return self._isValid
        else:
            return False

    def state(self):
        raise NotImplementedError()

    def updateState(self):
        self._oldState = self.state()

    def stateChanged(self):
        if self.isValid():
            return self.state() != self._oldState
        else:
            return True

    def clearCache(self):
        if self.isValid():
            # del <var1>, ..., <varN>
            raise NotImplementedError()


class DataFitter(DataHandlerBase):

    functions = (
        lambda x, a, b: a + b * x,  # linear
        lambda x, a, b, c: a + b * x + c * x ** 2,  # quadratic
        lambda x, a, b, c, d: a + b * x + c * x**2 + d * x**3,  # cubic
        lambda x, a, b: a * np.exp(b * x), # exponential
        lambda x, a, b: a + b * np.log(x) # logarithmic
    )

    def __init__(self, show, binner, curveFitFunction, modeCurveFitAll, modeCurveFitRoi):
        assert isinstance(show, QToolButton)
        assert isinstance(binner, DataBinner)
        assert isinstance(curveFitFunction, QComboBox)
        assert isinstance(modeCurveFitAll, QRadioButton)
        assert isinstance(modeCurveFitRoi, QRadioButton)
        self.show = show
        self.binner = binner
        self.curveFitFunction = curveFitFunction
        self.modeCurveFitAll = modeCurveFitAll
        self.modeCurveFitRoi = modeCurveFitRoi

    def state(self):
        return (
            self.binner.readerX.state(), self.binner.readerY.state(), self.binner.readerRoi.state(),
            self.curveFitFunction.currentIndex()
        )

    def setCache(self, fitAll, fitRoi):
        self._fitAll = fitAll
        self._fitRoi = fitRoi

    def clearCache(self):
        if self.isValid():
            del self._fitAll, self._fitRoi

    def fitPredict(self):

        if not self.show.isChecked():
            if self.stateChanged():
                self.setInvalidAndClearCache()
            return

        if self.stateChanged():
            if debug: print('fit')
            rangeX = self.binner.range()[0]
            self.f = self.functions[self.curveFitFunction.currentIndex()]
            plotX = np.linspace(start=rangeX[0], stop=rangeX[1], num=1000)

            # fit and predict all data
            if self.binner.readerX.isValid() and self.binner.readerY.isValid():
                mask = self.binner.maskAll()
                fitAll = self._fitPredict(mask=mask, plotX=plotX)
            else:
                fitAll = None

            # fit and predict roi data
            if self.binner.readerX.isValid() and self.binner.readerY.isValid() and self.binner.readerRoi.isValid():
                mask = self.binner.maskRoi()
                fitRoi = self._fitPredict(mask=mask, plotX=plotX)
            else:
                fitRoi = None

            self.setCache(fitAll=fitAll, fitRoi=fitRoi)
            self.setValid()
            self.updateState()
        else:
            if debug: print('fit (cached)')

    def _fitPredict(self, mask, plotX):

        # extract data
        x = self.binner.readerX.array()[mask]
        y = self.binner.readerY.array()[mask]

        # fit model
        try:
            popt, pcov = curve_fit(self.f, x, y)
        except:
            return None

        # assess performance
        yfit = self.f(x, *popt)
        rmse = np.sqrt(np.sum((y - yfit) ** 2))
        pearsonr_, pvalue = pearsonr(y, yfit)
        n = np.sum(mask)

        # predict plot data
        plotY = self.f(plotX, *popt)

        return {'popt': popt, 'pcov': pcov, 'rmse': rmse, 'pearsonr': pearsonr_, 'n': n,
                'plotX': plotX, 'plotY': plotY}

class DataOverlayer(DataHandlerBase):

    def __init__(self, show, binner, color, opacity, mapCanvas, imageView):
        assert isinstance(show, QToolButton)
        assert isinstance(binner, DataBinner)
        assert isinstance(color, QgsColorButton)
        assert isinstance(opacity, QSpinBox)
        assert isinstance(mapCanvas, QgsMapCanvas)
        assert isinstance(imageView, RdpScatterPlotImageViewWidget)
        self.show = show
        self.binner = binner
        self.color = color
        self.opacity = opacity
        self.mapCanvas = mapCanvas
        self.imageView = imageView

    def state(self):
        roiState = lambda roi: (roi.size(), roi.pos(), roi.angle())
        return (
            self.binner.state(),
            [roiState(roi) for roi in self.imageView.rois],
            self.opacity.value()
        )

    def setCache(self, rgba):
        self._rgba = rgba

    def clearCache(self):
        if self.isValid():
            del self._rgba

    def makePen(self):
        width = 1.0
        pen = QPen(QBrush(self.color.color()), width)
        pen.setCosmetic(True)
        return pen

    def createCircle(self):
        (minX, maxX), (minY, maxY) = self.imageView.range()
        s = maxX - minX, maxY - minY
        m = [v * 0.1 for v in s]
        roi = pg.EllipseROI(pos=(minX + m[0], minY + m[1]), size=[s[0] - 2*m[0], s[1] - 2*m[1]],
                            removable=True, pen=self.makePen(), rotatable=True, movable=True)
        self._createRoi(roi=roi)

    def createRectangle(self):
        (minX, maxX), (minY, maxY) = self.imageView.range()
        s = maxX - minX, maxY - minY
        m = [v * 0.1 for v in s]
        roi = pg.RectROI(pos=(minX + m[0], minY + m[1]), size=[s[0] - 2 * m[0], s[1] - 2 * m[1]],
                         removable=True, pen=self.makePen(), rotatable=True, movable=True)
        roi.addRotateHandle(pos=(1, 0), center=(0.5, 0.5))
        self._createRoi(roi=roi)

    def createPolygon(self):
        (minX, maxX), (minY, maxY) = self.imageView.range()
        s = maxX - minX, maxY - minY
        m = [v * 0.1 for v in s]
        roi = pg.PolyLineROI(positions=[(minX + m[0], minY + m[1]),
                                        (maxX - m[0], minY + m[1]),
                                        (minX / 2 + maxX / 2, maxY - m[1])],
                             closed=True, removable=True, pen=self.makePen(), rotatable=False, movable=True)
        self._createRoi(roi=roi)

    def _createRoi(self, roi):
        roi.sigRegionChangeFinished.connect(self.mapCanvas.refresh)
        roi.sigRemoveRequested.connect(self.mapCanvas.refresh)
        #roi.sigRegionChanged.connect(self.mapCanvas.refresh) # live update of map canvas is too slow!

        self.imageView.addRoi(roi=roi)
        self.mapCanvas.refresh()

    def overlay(self, painter):
        assert isinstance(painter, QPainter)

        if not self.binner.isValid():
            return

        if not self.show.isChecked() or not self.show.isEnabled():
            return

        if self.stateChanged():
            if debug: print('overlay')

            mask = self.binner.maskAll()
            h = self.binner.hAll()
            binIndices = self.binner.binIndicesAll()
            binsX, binsY = self.binner.bins()
            xsize = self.mapCanvas.size().width()
            ysize = self.mapCanvas.size().height()

            # Create buffer for overlay image calculations
            r = np.zeros_like(mask, dtype=np.uint8)
            g = np.zeros_like(mask, dtype=np.uint8)
            b = np.zeros_like(mask, dtype=np.uint8)
            a = np.zeros_like(mask, dtype=np.uint8)

            # Create lookup dict holding image locations grouped by bin locations
            imageIndices = np.where(mask)[0]
            binIndicesDict = {bin: list() for bin in binIndices}
            [binIndicesDict[bin].append(i) for bin, i in zip(binIndices, imageIndices)]
            binXIndexArray = (np.array(range(binsX)).reshape(1, binsX) * np.full(shape=(binsY, 1), fill_value=1))
            binYIndexArray = (np.array(range(binsY)).reshape(binsY, 1) * np.full(shape=(1, binsX), fill_value=1))

            # Create overlay image from ROIs.
            rois = self.imageView.rois

            # Pseudo-erase all pixels by setting setting the opacity to zero.
            a *= 0

            # Update overlay image with each individually colored roi
            img = self.imageView.getImageItem()
            for roi in rois:
                assert isinstance(roi, pg.ROI)
                selBinXIndexArray = roi.getArrayRegion(binXIndexArray.T, img=img).astype(np.int64)
                selBinYIndexArray = roi.getArrayRegion(binYIndexArray.T, img=img).astype(np.int64)
                selBinIndexArray = (1000000 + selBinXIndexArray * 1000. + selBinYIndexArray).astype(np.int64)
                selHArray = roi.getArrayRegion(h, img=img).astype(np.int64)
                nonEmptyBins = selBinIndexArray[selHArray != 0]

                color = roi.pen.color()
                imageIndices = list()
                for bin in nonEmptyBins:
                    imageIndicesForTheBin = binIndicesDict.get(bin, None)
                    if imageIndicesForTheBin is None:
                        continue
                    imageIndices.extend(imageIndicesForTheBin)

                r[imageIndices] = color.red()
                g[imageIndices] = color.green()
                b[imageIndices] = color.blue()
                a[imageIndices] = int(2.5 * self.opacity.value())

            r = r.reshape(ysize, xsize)
            g = g.reshape(ysize, xsize)
            b = b.reshape(ysize, xsize)
            a = a.reshape(ysize, xsize)

            rgba = np.array([b, g, r, a]).transpose([1, 2, 0])
            rgba = np.require(rgba, np.uint8, 'C')
            self.setCache(rgba=rgba)
            self.setValid()
            self.updateState()
        else:
            if debug: print('overlay (cached)')
            rgba = self._rgba

        qrgba = QImage(rgba.data, rgba.shape[1], rgba.shape[0], rgba.strides[0], QImage.Format_ARGB32)
        painter.drawImage(QRect(QPoint(0, 0), qrgba.size()), qrgba)


class DataPlotter():

    def __init__(self, binner, fitter, imageView, colorRampAll, colorRampRoi, colorAll, colorRoi,
                 oneToOneColor, curveFitColor, curveFitLabel):

        assert isinstance(binner, DataBinner)
        assert isinstance(fitter, DataFitter)
        assert isinstance(imageView, RdpScatterPlotImageViewWidget)
        assert isinstance(colorRampAll, QgsColorRampButton)
        assert isinstance(colorRampRoi, QgsColorRampButton)
        assert isinstance(colorAll, QgsColorButton)
        assert isinstance(colorRoi, QgsColorButton)
        assert isinstance(oneToOneColor, QgsColorButton)
        assert isinstance(curveFitColor, QgsColorButton)
        assert isinstance(curveFitLabel, QPlainTextEdit)
        self.binner = binner
        self.fitter = fitter
        self.imageView = imageView
        self.colorRampAll = colorRampAll
        self.colorRampRoi = colorRampRoi
        self.colorAll = colorAll
        self.colorRoi = colorRoi
        self.oneToOneColor = oneToOneColor
        self.curveFitColor = curveFitColor
        self.curveFitLabel = curveFitLabel


    def plotImage(self, range,
                  stretchAll, showAll, showAllDensity, showAllScatter,
                  stretchRoi, showRoi, showRoiDensity, showRoiScatter, showRoiStyled):

        self._rangeX, self._rangeY = range
        self._binsX, self._binsY = self.binner.hAll().shape
        self._scaleX = (self._rangeX[1] - self._rangeX[0]) / float(self._binsX)
        self._scaleY = (self._rangeY[1] - self._rangeY[0]) / float(self._binsY)
        self._stretchAll = stretchAll
        self._stretchRoi = stretchRoi

        if not showAll:
            rgbaAll = np.full(shape=(self._binsX, self._binsY, 4), fill_value=0, dtype=np.uint8)
        elif showAllDensity:
            rgbaAll = self._renderDensityAll()
        elif showAllScatter:
            rgbaAll = self._renderScatterAll()
        else:
            assert 0

        if not showRoi or not self.binner.readerRoi.isValid() :
            rgbaRoi = np.full(shape=(self._binsX, self._binsY, 4), fill_value=0, dtype=np.uint8)
        elif showRoiDensity:
            rgbaRoi = self._renderDensityRoi()
        elif showRoiScatter:
            rgbaRoi = self._renderScatterRoi()
        elif showRoiStyled:
            rgbaRoi = self._renderStyledRoi()
        else:
            assert 0

        rgba = self._blendImageOnTopOfBackground(background=rgbaAll, image=rgbaRoi)

        self.imageView.plotItem().blockSignals(True)
        self.imageView.getImageItem().blockSignals(True)
        self.imageView.setImage(rgba, pos=[self._rangeX[0], self._rangeY[0]],
                                scale=[self._scaleX, self._scaleY], autoRange=False)
        self.imageView.plotItem().blockSignals(False)
        self.imageView.getImageItem().blockSignals(False)

    def _blendImageOnTopOfBackground(self, background, image):
        rgba = background.copy()
        mask = image[:,:,3] == 255
        for i in range(4):
            rgba[:,:,i][mask] = image[:,:,i][mask]
        return rgba

    def _colorMapFromColorRamp(self, colorRamp):
        assert isinstance(colorRamp, QgsColorRamp)
        array = np.empty(shape=(256, 3), dtype=np.uint8)
        for i in range(256):
            color = colorRamp.color(i / 255)
            assert isinstance(color, QColor)
            array[i, 0] = color.red()
            array[i, 1] = color.green()
            array[i, 2] = color.blue()
        return array

    def _renderAsRgba(self, image, stretch, colorRamp):

        ###test
        #array = np.empty((256, 3))
        #abytes = np.arange(0, 1, 0.00390625)
        #array[:, 0] = np.abs(2 * abytes - 0.5) * 255
        #array[:, 1] = np.sin(abytes * np.pi) * 255
        #array[:, 2] = np.cos(abytes * np.pi / 2) * 255
        ######

        lookupTable = self._colorMapFromColorRamp(colorRamp=colorRamp)

        self.imageView.plotItem().blockSignals(True)
        self.imageView.getImageItem().blockSignals(True)
        try:
            self.imageView.setImage(image, pos=[self._rangeX[0], self._rangeY[0]],
                                    scale=[self._scaleX, self._scaleY], autoRange=False)
            self.imageView.getImageItem().setLookupTable(lookupTable)
            self.imageView.setLevels(*stretch)
            self.imageView.getHistogramWidget().item.setHistogramRange(*stretch)
        except:
            pass
        rgba = self.imageView.renderedImage()
        return rgba

    def _renderDensityAll(self):
        h = self.binner.hAll()
        rgba = self._renderAsRgba(image=h, stretch=self._stretchAll, colorRamp=self.colorRampAll.colorRamp())
        rgba[:, :, 3][h == 0] = 0
        return rgba

    def _renderDensityRoi(self):
        h = self.binner.hRoi()
        rgba = self._renderAsRgba(image=h, stretch=self._stretchRoi, colorRamp=self.colorRampRoi.colorRamp())
        rgba[:, :, 3][h == 0] = 0
        return rgba

    def _renderScatterAll(self):
        mask = self.binner.hAll() > 0
        rgba = np.full(shape=(self._binsX, self._binsY, 4), fill_value=0, dtype=np.uint8)
        color = self.colorAll.color()
        assert isinstance(color, QColor)
        for i, v in enumerate([color.red(), color.green(), color.blue()]):
            #rgba[:, :, i][[mask]] = v
            rgba[:, :, i][mask] = v

        rgba[:,:,3][mask] = 255
        return rgba

    def _renderScatterRoi(self):
        mask = self.binner.hRoi() > 0
        rgba = np.full(shape=(self._binsX, self._binsY, 4), fill_value=0, dtype=np.uint8)
        color = self.colorRoi.color()
        assert isinstance(color, QColor)
        for i, v in enumerate([color.red(), color.green(), color.blue()]):
            rgba[:,:,i][[mask]] = v
        rgba[:,:,3][mask] = 255
        return rgba

    def _renderStyledRoi(self):

        def hByMaskColor(color, x, y, maskColor, range, bins):  # color format is 1RRRGGGBBB
            valid = maskColor == color
            r = binned_statistic_2d(x=x[valid], y=y[valid], values=x, statistic='count', bins=bins,
                                    range=range, expand_binnumbers=True)
            h = r.statistic
            return h

        maskColor = self.binner.readerRoi.color()
        x = self.binner.readerX.array()
        y = self.binner.readerY.array()

        h_sum = np.zeros(shape=(self._binsX, self._binsY))
        r = np.zeros(shape=(self._binsX, self._binsY))
        g = np.zeros(shape=(self._binsX, self._binsY))
        b = np.zeros(shape=(self._binsX, self._binsY))

        for color in np.unique(maskColor):
            if color == -1: continue

            h_fid = hByMaskColor(color=color, x=x, y=y, maskColor=maskColor, range=(self._rangeX, self._rangeY),
                                 bins=(self._binsX, self._binsY))
            h_sum += h_fid
            valid = h_fid != 0

            r[valid] += h_fid[valid] * int(color % 1000000000 / 1000000)
            g[valid] += h_fid[valid] * int(color % 1000000 / 1000)
            b[valid] += h_fid[valid] * int(color % 1000)

        with np.warnings.catch_warnings():
            np.warnings.filterwarnings('ignore', r'invalid value encountered in true_divide')
            r /= h_sum
            g /= h_sum
            b /= h_sum

        rgba = np.full(shape=(self._binsX, self._binsY, 4), fill_value=0, dtype=np.uint8)
        rgba[:, :, 0] = r.astype(np.uint8)
        rgba[:, :, 1] = g.astype(np.uint8)
        rgba[:, :, 2] = b.astype(np.uint8)

        mask = self.binner.hRoi() > 0
        rgba[:,:,3][mask] = 255
        return rgba

    def plotFittedCurve(self, show):

        clear = False
        if show:
            sign = lambda coeff: '-' if coeff < 0 else '+'
            ndigits = 4

            if self.fitter.modeCurveFitAll.isChecked():
                fit = self.fitter._fitAll
            elif self.fitter.modeCurveFitRoi.isChecked():
                fit = self.fitter._fitRoi
            else:
                assert 0

            if fit is None:
                clear = True
            else:
                popt = fit['popt']
                r = fit['pearsonr']
                rmse = fit['rmse']
                n = fit['n']
                p = [round(v, ndigits) for v in popt]
                if self.fitter.f == self.fitter.functions[0]:
                    text = 'f(x) = {} {} {} * x'.format(p[0], sign(p[1]), abs(p[1]))
                elif self.fitter.f == self.fitter.functions[1]:
                    text = 'f(x) = {} {} {} * x {} {} * x**2'.format(p[0], sign(p[1]), abs(p[1]),
                                                                     sign(p[2]), abs(p[2]))
                elif self.fitter.f == self.fitter.functions[2]:
                    text = 'f(x) = {} {} {} * x {} {} * x**2 {} {} * x**3'.format(p[0], sign(p[1]), abs(p[1]),
                                                                                  sign(p[2]), abs(p[2]),
                                                                                  sign(p[3]), abs(p[3]))
                elif self.fitter.f == self.fitter.functions[3]:
                    text = 'f(x) = {} * exp({} {} * x)'.format(p[0], sign(p[1]), abs(p[1]))
                elif self.fitter.f == self.fitter.functions[4]:
                    text = 'f(x) = {} {} {} * log(x)'.format(p[0], sign(p[1]), abs(p[1]))
                else:
                    assert 0

                text += ' | r^2 = {} | rmse = {} | n = {}'.format(str(round(r**2, 4)), str(round(rmse**2, 4)), n)
                from ..site import pyqtgraph as pg

                #self.imageView.fittedCurve().blockSignals(True)
                self.imageView.fittedCurve().setPen(pg.mkPen(color=self.curveFitColor.color(), width=1, style=Qt.SolidLine))
                self.imageView.fittedCurve().setData(fit['plotX'], fit['plotY'])
                #self.imageView.fittedCurve().blockSignals(False)
                self.curveFitLabel.setPlainText(text)
        else:
            clear = True

        if clear:
            self.clearFittedCurve()

    def plotOneToOne(self, show):
        if show:
            (minX, maxX), (minY, maxY) = self.binner.range()
            self.imageView.oneToOne().setPen(pg.mkPen(color=self.oneToOneColor.color(), width=1, style=Qt.SolidLine))
            x = y = np.linspace(start=min(minX, minY), stop=max(maxX, maxY), num=100)
            self.imageView.oneToOne().setData(x, y)

        else:
            self.imageView.oneToOne().clear()

    def setRange(self, range):
        self.imageView.setRange(range=range)
        self.imageView.update()

    def clearImage(self):
        rgba = self.imageView.renderedImage()
        # ensure none zero data range
        rgba[0, 0, :-1] = 0
        rgba[0, 1, :] = 1
        # set transparent
        rgba[: , :, 3] = 0
        self.imageView.setImage(rgba, autoRange=False)

    def clearFittedCurve(self):
        self.imageView.fittedCurve().clear()
        self.curveFitLabel.setPlainText('')

class DataBinner(DataHandlerBase):

    def __init__(self, readerX, readerY, readerRoi):
        assert isinstance(readerX, DataReader)
        assert isinstance(readerY, DataReader)
        assert isinstance(readerRoi, DataReaderRoi)
        self.readerX = readerX
        self.readerY = readerY
        self.readerRoi = readerRoi

    def state(self):
        return (
            self.readerX.state(), self.readerY.state(), self.readerRoi.state(),
            self.readerX.min.text(), self.readerX.max.text(), self.readerX.bins.value(),
            self.readerY.min.text(), self.readerY.max.text(), self.readerY.bins.value(),
        )

    def setCacheAll(self, stretchPercentilesAll, hAll, binIndicesAll, maskAll, bins, range):
        self._stretchPercentilesAll = stretchPercentilesAll
        self._hAll = hAll
        self._binIndicesAll = binIndicesAll
        self._maskAll = maskAll
        self._bins = bins
        self._range = range

    def setCacheRoi(self, stretchPercentilesRoi, hRoi, maskRoi):
        self._stretchPercentilesRoi = stretchPercentilesRoi
        self._hRoi = hRoi
        self._maskRoi = maskRoi

    def clearCache(self):
        if self.isValid():
            del self._stretchPercentilesAll, self._hAll, self._binIndicesAll, self._maskAll, self._bins, self._range
            if self.readerRoi.isValid():
                del self._stretchPercentilesRoi, self._hRoi, self._maskRoi

    def bin(self, bins, range):

        if self.stateChanged():

            # Calculate count distribution for map canvas
            if self.readerX.isValid() and self.readerY.isValid():
                maskAll = np.logical_and(self.readerX.mask(), self.readerY.mask())
                x = self.readerX.array()[maskAll]
                y = self.readerY.array()[maskAll]

                r = binned_statistic_2d(x=x, y=y,
                                        bins=bins, range=range,
                                        values=x, statistic='count', expand_binnumbers=True)
                h = r.statistic
                binIndices = (1000000 + (r.binnumber[0] - 1) * 1000 + r.binnumber[1] - 1).flatten()
            else:
                h = np.zeros(shape=bins)
                maskAll = False
                binIndices = None

            self.setCacheAll(stretchPercentilesAll=self._calculateStretchPercentiles(h=h),
                             hAll = h.astype(np.int64), binIndicesAll = binIndices,
                             maskAll=maskAll, bins=bins, range=range)

            # Calculate count distribution for region of interest
            if self.readerX.isValid() and self.readerY.isValid() and self.readerRoi.isValid():

                maskRoi = np.logical_and(maskAll, self.readerRoi.mask())
                x = self.readerX.array()[maskRoi]
                y = self.readerY.array()[maskRoi]
                r = binned_statistic_2d(x=x, y=y,
                                        bins=bins, range=range,
                                        values=x, statistic='count', expand_binnumbers=True)
                h = r.statistic
            else:
                maskRoi = False
                h = np.zeros(shape=bins)

            self.setCacheRoi(stretchPercentilesRoi=self._calculateStretchPercentiles(h=h),
                             hRoi=h.astype(np.int64),
                             maskRoi=maskRoi)

            self.setValid()
            self.updateState()
            if debug: print('bin')
        else:
            if debug: print('bin (cached)')

    def _calculateStretchPercentiles(self, h):
        q = builtins.range(1001)
        p = np.percentile(h, [v / 10 for v in q])
        return dict(zip(q, p))

    def hAll(self):
        return self._hAll

    def hRoi(self):
        return self._hRoi

    def stretchAll(self, p):
        return self._stretchPercentilesAll[int(p * 10)]

    def stretchRoi(self, p):
        return self._stretchPercentilesRoi[int(p * 10)]

    def binIndicesAll(self):
        return self._binIndicesAll

    def maskAll(self):
        return self._maskAll

    def maskRoi(self):
        return self._maskRoi

    def bins(self):
        return self._bins

    def range(self):
        return self._range


class DataReader(DataHandlerBase):

    def __init__(self, axis, mapCanvas, modeDataExtentWholeRaster, modeDataExtentMapCanvas, referenceLayer):
        assert isinstance(axis, RdpAxisWidget)
        assert isinstance(mapCanvas, QgsMapCanvas)
        assert isinstance(modeDataExtentWholeRaster, QRadioButton)
        assert isinstance(modeDataExtentMapCanvas, QRadioButton)
        assert isinstance(referenceLayer, QgsMapLayerComboBox)
        self.axis = axis
        self.layer = axis.ui.layer()
        self.modeRaster = axis.ui.modeRaster()
        self.band = axis.ui.band()
        self.modeTimeseries = axis.ui.modeTimeseries()
        self.date = axis.ui.date()
        self.name = axis.ui.name()
        self.min = axis.ui.min()
        self.max = axis.ui.max()
        self.bins = axis.ui.bins()
        self.mapCanvas = mapCanvas
        self.modeDataExtentWholeRaster = modeDataExtentWholeRaster
        self.modeDataExtentMapCanvas = modeDataExtentMapCanvas
        self.referenceLayer = referenceLayer

    def setCache(self, array, mask, range):
        self._array = array
        self._mask = mask
        self._range = range

    def clearCache(self):
        if self.isValid():
            del self._array, self._mask, self._range

    def state(self):
        if self.modeDataExtentMapCanvas.isChecked():
            return (
                self.layer.currentLayer(), self.band.currentIndex(), self.date.currentIndex(), self.name.currentIndex(),
                self.mapCanvas.extent(), self.mapCanvas.size(), self.mapCanvas.mapSettings().destinationCrs()
            )
        elif self.modeDataExtentWholeRaster.isChecked():
            return (
                self.layer.currentLayer(), self.band.currentIndex(), self.date.currentIndex(), self.name.currentIndex(),
                self.referenceLayer.currentLayer(),
            )

    def read(self):

        if self.stateChanged():
            if self.modeDataExtentMapCanvas.isChecked():
                self._readMapCanvas()
            elif self.modeDataExtentWholeRaster.isChecked():
                self._readWholeRaster()
            self.updateState()
        else:
            if debug: print('read (cached)')

    def _read(self, extent, size, crs):
        assert isinstance(extent, QgsRectangle)
        assert isinstance(size, QSize)
        assert isinstance(crs, QgsCoordinateReferenceSystem)

        layer = self.layer.currentLayer()

        if layer is None or layer.source() == '':
            self.setInvalidAndClearCache()
            return

        if self.modeRaster.isChecked():
            band = self.band.currentIndex() + 1
        elif self.modeTimeseries.isChecked():
            timeseries = self.date.timeseries()
            band = timeseries.numberOfBands() * self.date.currentIndex() + self.name.currentIndex() + 1
        else:
            assert 0

        assert isinstance(layer, QgsRasterLayer)
        assert isinstance(band, int) and band > 0 and band <= layer.bandCount(), band

        provider = layer.dataProvider()
        assert isinstance(provider, QgsRasterDataProvider)

        # setup on-the-fly resampling if needed
        if crs != layer.crs():
            #projector = QgsRasterProjector()
            #projector.setCrs(layer.crs(), crs)
            pipe = QgsRasterPipe()
            pipe.set(provider.clone())
            projector = QgsRasterProjector()
            projector.setCrs(layer.crs(), crs)
            pipe.insert(2, projector)
        else:
            projector = provider

        # read data
        block = projector.block(band, extent, size.width(), size.height())
        assert isinstance(block, QgsRasterBlock)
        array = np.frombuffer(np.array(np.array(block.data())),
                              dtype=rdputils.qgisDataTypeToNumpyDataType(block.dataType()))

        # calculate mask from band layer
        mask = np.full_like(array, fill_value=True, dtype=np.bool)
        noDataValues = [obj.min() for obj in provider.userNoDataValues(band)]
        if provider.sourceHasNoDataValue(band) and provider.useSourceNoDataValue(band):
            noDataValues.append(provider.sourceNoDataValue(band))

        for noDataValue in noDataValues:
            mask[array == noDataValue] = False

        data = array[mask]

        if data.size == 0:
            self.setInvalidAndClearCache()
            return

        range = data.min(), data.max()

        self.setCache(array=array, mask=mask, range=range)
        self.setValid()

    def _readMapCanvas(self):
        if debug: print('readMapCanvas')
        self._read(extent=self.mapCanvas.extent(),
                   size=self.mapCanvas.size(),
                   crs=self.mapCanvas.mapSettings().destinationCrs())

    def _readWholeRaster(self):
        referenceLayer = self.referenceLayer.currentLayer()
        if isinstance(referenceLayer, QgsRasterLayer):
            if debug: print('readWholeRaster')
            self._read(extent=referenceLayer.extent(),
                       size=QSize(referenceLayer.width(), referenceLayer.height()),
                       crs=referenceLayer.crs())
        else:
            self.setInvalidAndClearCache()

    def array(self):
        return self._array

    def mask(self):
        return self._mask

    def range(self):
        return self._range


class DataReaderRoi(DataHandlerBase):

    def __init__(self, layer, mapCanvas, modeDataExtentWholeRaster, modeDataExtentMapCanvas, referenceLayer):
        assert isinstance(layer, QgsMapLayerComboBox)
        assert isinstance(mapCanvas, QgsMapCanvas)
        assert isinstance(modeDataExtentWholeRaster, QRadioButton)
        assert isinstance(modeDataExtentMapCanvas, QRadioButton)
        assert isinstance(referenceLayer, QgsMapLayerComboBox)
        self.layer = layer
        self.mapCanvas = mapCanvas
        self.modeDataExtentWholeRaster = modeDataExtentWholeRaster
        self.modeDataExtentMapCanvas = modeDataExtentMapCanvas
        self.referenceLayer = referenceLayer

    def state(self):

        if self.modeDataExtentMapCanvas.isChecked():
            return (
                self.layer.currentLayer(),
                self.mapCanvas.extent(), self.mapCanvas.size(), self.mapCanvas.mapSettings().destinationCrs()
            )
        elif self.modeDataExtentWholeRaster.isChecked():
            return self.layer.currentLayer(), self.referenceLayer.currentLayer()


    def setCache(self, color, mask):
        self._color = color
        self._mask = mask

    def clearCache(self):
        if self.isValid():
            del self._color, self._mask

    def read(self):

        if self.stateChanged():

            layer = self.layer.currentLayer()

            if layer is None or layer.source() == '':
                self.setInvalidAndClearCache()
                return

            if self.modeDataExtentMapCanvas.isChecked():
                self._readMapCanvas()
            elif self.modeDataExtentWholeRaster.isChecked():
                self._readWholeRaster()

            self.updateState()
            self.setValid()

            if debug: print('readRoi')
        else:
            if debug: print('readRoi (cached)')

    def _readMapCanvas(self):
        self._rasterizeColor(extent=self.mapCanvas.extent(),
                             size=self.mapCanvas.size(),
                             crs=self.mapCanvas.mapSettings().destinationCrs(),
                             allTouched=False)

    def _readWholeRaster(self):
        referenceLayer = self.referenceLayer.currentLayer()
        assert isinstance(referenceLayer, QgsRasterLayer)
        self._rasterizeColor(extent=referenceLayer.extent(),
                             size=QSize(referenceLayer.width(), referenceLayer.height()),
                             crs=referenceLayer.crs(),
                             allTouched=False)

    def _rasterizeColor(self, extent, size, crs, allTouched=False):
        '''Returns color code array for the current style in the format 1RRRGGGBBB.'''

        assert isinstance(extent, QgsRectangle)
        assert isinstance(size, QSize)
        assert isinstance(crs, QgsCoordinateReferenceSystem)

        layer = self.layer.currentLayer()
        assert isinstance(layer, QgsVectorLayer)
        onlySelectedFeatures = layer.selectedFeatureCount() > 0

        # Create reprojected temp layer with selected features only
        filename = '/vsimem/rasterdataplotting/mask.gpkg'
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.fileEncoding = 'System'
        options.ct = QgsCoordinateTransform(crs, layer.crs(), QgsProject.instance())
        options.driverName = 'GPKG'
        options.onlySelectedFeatures = onlySelectedFeatures
        options.skipAttributeCreation = False
        options.filterExtent = extent
        QgsVectorFileWriter.writeAsVectorFormat(layer, filename, options)

        # Get renderer colors.
        renderer = layer.renderer()
        defaultColor = QColor('red')

        if isinstance(renderer, QgsInvertedPolygonRenderer):
            renderer = renderer.embeddedRenderer()

        if isinstance(renderer, QgsCategorizedSymbolRenderer):

            def getColor(feature):
                try:
                    legendClassificationAttribute = renderer.legendClassificationAttribute()
                    legendClassificationValue = feature.GetField(legendClassificationAttribute)
                    categoryIndex = renderer.categoryIndexForValue(legendClassificationValue)
                    category = renderer.categories()[categoryIndex]
                    color = category.symbol().color()
                except:
                    traceback.print_exc()
                    color = defaultColor
                return color

        elif isinstance(renderer, QgsGraduatedSymbolRenderer):

            def getColor(feature):
                try:
                    legendClassificationAttribute = renderer.legendClassificationAttribute()
                    legendClassificationValue = feature.GetField(legendClassificationAttribute)
                    color = renderer.symbolForValue(legendClassificationValue).color()

                except:
                    traceback.print_exc()
                    color = defaultColor
                return color

        elif isinstance(renderer, QgsSingleSymbolRenderer):

            getColor = lambda feature: renderer.symbol().color()

        else:

            getColor = lambda feature: defaultColor

        # Create another memory layer to add COLOR field coded as 1RRRGGGBBB integer.
        vds1 = ogr.Open(filename)
        layer1 = vds1.GetLayerByIndex(0)
        assert isinstance(layer1, ogr.Layer)

        driver = ogr.GetDriverByName('Memory')
        vds2 = driver.CreateDataSource('wrk')
        srs = osr.SpatialReference(crs.toWkt())

        # - create layer
        geom_type = layer1.GetGeomType()
        layer2 = vds2.CreateLayer('layer', srs=srs, geom_type=geom_type)
        assert isinstance(layer2, ogr.Layer)

        # - create field
        field = ogr.FieldDefn('_COLOR', ogr.OFTInteger)
        layer2.CreateField(field)

        # - create features and set values
        encodeColor = lambda qcolor: 1000000000 + qcolor.red() * 1000000 + qcolor.green() * 1000 + qcolor.blue()
        for feature in layer1:
            assert isinstance(feature, ogr.Feature)
            color = encodeColor(getColor(feature))
            outFeature = ogr.Feature(layer2.GetLayerDefn())
            outFeature.SetGeometry(feature.GetGeometryRef())
            outFeature.SetField('_COLOR', color)
            layer2.CreateFeature(outFeature)

        # Free memory.
        vds1 = None
        gdal.Unlink(filename)

        # Rasterize COLOR.
        xmin = extent.xMinimum()
        xmax = extent.xMaximum()
        ymin = extent.yMinimum()
        ymax = extent.yMaximum()
        xsize = size.width()
        ysize = size.height()
        xres = (xmax - xmin) / xsize
        yres = (ymax - ymin) / ysize
        geotransform = (xmin, xres, 0.0, ymax, 0.0, -yres)
        gdalType = gdal.GDT_Int32
        initValue = -1
        burnAttribute = '_COLOR'
        filename = ''
        driver = gdal.GetDriverByName('MEM')
        #filename = 'c:/vsimem/rasterdataplotting/rasterFid.bsq'
        #driver = gdal.GetDriverByName('ENVI')

        ds = driver.Create(filename, xsize, ysize, 1, gdalType)
        assert isinstance(ds, gdal.Dataset)
        ds.GetRasterBand(1).Fill(initValue)
        ds.SetProjection(crs.toWkt())
        ds.SetGeoTransform(geotransform)

        rasterizeLayerOptions = list()
        if allTouched:
            rasterizeLayerOptions.append('ALL_TOUCHED=TRUE')
        if burnAttribute is not None:
            rasterizeLayerOptions.append('ATTRIBUTE=' + burnAttribute)

        gdal.RasterizeLayer(ds, [1], layer2, options=rasterizeLayerOptions)
        color = ds.ReadAsArray().flatten()
        mask = color != -1

        self.setCache(color=color, mask=mask)
        self.setValid()

    def color(self):
        return self._color

    def mask(self):
        return self._mask

class _Ui(object):

    def __init__(self, obj):
        self.obj = obj

    def axisX(self):
        assert isinstance(self.obj._axisX, RdpAxisWidget)
        return self.obj._axisX

    def axisY(self):
        assert isinstance(self.obj._axisY, RdpAxisWidget)
        return self.obj._axisY

    def imageView(self):
        assert isinstance(self.obj._imageView, RdpScatterPlotImageViewWidget)
        return self.obj._imageView

    # data extent group
    def showPlot(self):
        assert isinstance(self.obj._showPlot, QToolButton)
        return self.obj._showPlot

    def modeDataExtentWholeRaster(self):
        assert isinstance(self.obj._modeDataExtentWholeRaster, QRadioButton)
        return self.obj._modeDataExtentWholeRaster

    def modeDataExtentMapCanvas(self):
        assert isinstance(self.obj._modeDataExtentMapCanvas, QRadioButton)
        return self.obj._modeDataExtentMapCanvas

    # all data group
    def showAll(self):
        assert isinstance(self.obj._showAll, QToolButton)
        return self.obj._showAll

    def modeDensityAll(self):
        assert isinstance(self.obj._modeDensityAll, QRadioButton)
        return self.obj._modeDensityAll

    def modeScatterAll(self):
        assert isinstance(self.obj._modeScatterAll, QRadioButton)
        return self.obj._modeScatterAll

    def densityColorRampAll(self):
        assert isinstance(self.obj._densityColorRampAll, QgsColorRampButton)
        return self.obj._densityColorRampAll

    def densityStretchAll(self):
        assert isinstance(self.obj._densityStretchAll, QDoubleSpinBox)
        return self.obj._densityStretchAll

    def scatterColorAll(self):
        assert isinstance(self.obj._scatterColorAll, QgsColorButton)
        return self.obj._scatterColorAll

    # roi data group
    def showRoi(self):
        assert isinstance(self.obj._showRoi, QToolButton)
        return self.obj._showRoi

    def modeDensityRoi(self):
        assert isinstance(self.obj._modeDensityRoi, QRadioButton)
        return self.obj._modeDensityRoi

    def modeScatterRoi(self):
        assert isinstance(self.obj._modeScatterRoi, QRadioButton)
        return self.obj._modeScatterRoi

    def modeStyledRoi(self):
        assert isinstance(self.obj._modeStyledRoi, QRadioButton)
        return self.obj._modeStyledRoi

    def densityColorRampRoi(self):
        assert isinstance(self.obj._densityColorRampRoi, QgsColorRampButton)
        return self.obj._densityColorRampRoi

    def densityStretchRoi(self):
        assert isinstance(self.obj._densityStretchRoi, QDoubleSpinBox)
        return self.obj._densityStretchRoi

    def scatterColorRoi(self):
        assert isinstance(self.obj._scatterColorRoi, QgsColorButton)
        return self.obj._scatterColorRoi

    def styledReapplyRoi(self):
        assert isinstance(self.obj._styledReapplyRoi, QToolButton)
        return self.obj._styledReapplyRoi

    def layerRoi(self):
        assert isinstance(self.obj._layerRoi, QgsMapLayerComboBox)
        return self.obj._layerRoi

    # spectral roi group
    def showSpectralRoi(self):
        assert isinstance(self.obj._showSpectralRoi, QToolButton)
        return self.obj._showSpectralRoi

    def roiCircle(self):
        assert isinstance(self.obj._roiCircle, QToolButton)
        return self.obj._roiCircle

    def roiRectangle(self):
        assert isinstance(self.obj._roiRectangle, QToolButton)
        return self.obj._roiRectangle

    def roiPolygon(self):
        assert isinstance(self.obj._roiPolygon, QToolButton)
        return self.obj._roiPolygon

    def roiColor(self):
        assert isinstance(self.obj._roiColor, QgsColorButton)
        return self.obj._roiColor

    def roiOpacity(self):
        assert isinstance(self.obj._roiOpacity, QSpinBox)
        return self.obj._roiOpacity

    # curve fit group
    def showCurveFit(self):
        assert isinstance(self.obj._showCurveFit, QToolButton)
        return self.obj._showCurveFit

    def modeCurveFitAll(self):
        assert isinstance(self.obj._modeCurveFitAll, QRadioButton)
        return self.obj._modeCurveFitAll

    def modeCurveFitRoi(self):
        assert isinstance(self.obj._modeCurveFitRoi, QRadioButton)
        return self.obj._modeCurveFitRoi

    def curveFitFunction(self):
        assert isinstance(self.obj._curveFitFunction, QComboBox)
        return self.obj._curveFitFunction

    def curveFitColor(self):
        assert isinstance(self.obj._curveFitColor, QgsColorButton)
        return self.obj._curveFitColor

    def curveFitSolution(self):
        assert isinstance(self.obj._curveFitSolution, QPlainTextEdit)
        return self.obj._curveFitSolution

    # 1:1 line group
    def showOneToOne(self):
        assert isinstance(self.obj._showOneToOne, QToolButton)
        return self.obj._showOneToOne

    def oneToOneColor(self):
        assert isinstance(self.obj._oneToOneColor, QgsColorButton)
        return self.obj._oneToOneColor

