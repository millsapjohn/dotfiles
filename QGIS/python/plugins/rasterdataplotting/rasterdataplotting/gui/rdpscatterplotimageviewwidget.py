import numpy as np
from qgis.PyQt.QtCore import *

from ..site import pyqtgraph as pg

class RdpScatterPlotImageViewWidget(pg.ImageView):

    sigRangeChanged = pyqtSignal(object)

    def __init__(self, *args, **kwargs):

        self._plotItem = pg.PlotItem()
        pg.ImageView.__init__(self, *args, view=self._plotItem, **kwargs)

        self._initUi()
        self._connectSignals()
        self.rois = list()

    def _initUi(self):
        self.view.invertY(False)
        self.plotItem().setAspectLocked(lock=False)
        self._initImage()
        self.ui.menuBtn.hide()
        self.ui.roiBtn.hide()
        self.ui.histogram.hide()

        self._fittedCurve = self.plotItem().plot([0, 0],[0, 0], pen=pg.mkPen(color=(255, 0, 0), width=1,
                                                                            style=Qt.SolidLine))
        self._oneToOne = self.plotItem().plot([0, 0],[0, 0], pen=pg.mkPen(color=(255, 0, 0), width=1,
                                                                            style=Qt.SolidLine))

    def _connectSignals(self):
        self.plotItem().sigRangeChanged.connect(self.onRangeChanged)

    def onRangeChanged(self, *args):
        self.sigRangeChanged.emit(self.range())

    def _initImage(self):
        self.plotItem().blockSignals(True)
        self.getImageItem().blockSignals(True)
        self.setImage(np.array([[0.00001, 0]]), autoLevels=False, levels=[0.00001, 0.00001], autoRange=False)  # need to initialize image to properly calculate native screen resolution
        self.plotItem().blockSignals(False)
        self.getImageItem().blockSignals(False)

    def range(self):
        rangeX, rangeY = self.plotItem().getViewBox().state['viewRange']
        return tuple(rangeX), tuple(rangeY)

    def setRange(self, range):
        rangeX, rangeY = range
        self.plotItem().getViewBox().blockSignals(True)
        self.plotItem().getViewBox().setRange(xRange=rangeX, yRange=rangeY, padding=0, update=True, disableAutoRange=True)
        self.plotItem().getViewBox().blockSignals(False)
        self.plotItem().getViewBox().update()

    def setStretch(self, stretch):
        self.setLevels(*stretch)
        self.getHistogramWidget().item.setHistogramRange(*stretch)

    def addRoi(self, roi):
        assert isinstance(roi, pg.ROI)
        zvalue = 10 + len(self.rois)
        roi.setZValue(zvalue)

        def removeRoi(*args):
            self.view.removeItem(roi)
            self.rois.remove(roi)

        roi.sigRemoveRequested.connect(removeRoi)
        roi.show()
        self.view.addItem(roi)
        self.rois.append(roi)

    def plotItem(self):
        assert isinstance(self._plotItem, pg.PlotItem)
        return self._plotItem

    def renderedImage(self):
        img = self.getProcessedImage()
        self.getImageItem().render()
        qimage = self.getImageItem().qimage
        rgba_ = qimage.data # (b, g, b, a)
        rgba = np.full(shape=(qimage.width(), qimage.height(), 4), fill_value=255) # (r, g, b, a)
        for i in range(3):
            rgba[:,:,i] = rgba_[:,:,2-i].T
        return rgba

    def fittedCurve(self):
        return self._fittedCurve

    def oneToOne(self):
        return self._oneToOne

    def timeout(self):
        pass # turn dead
