import math
from os.path import join, dirname
from qgis.core import *
from qgis.gui import *
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *

from .. import rdputils
from .. import ui

from ..site import rastertimeseriesmanager as rtm

class RdpAxisWidget(QWidget):

    sigAxisChanged = pyqtSignal(object)
    sigLocationChanged = pyqtSignal()

    class Mode(object):
        Undefined = 0
        Band = 1
        SpectralProfile = 2
        TemporalProfile = 3

    class ModeLayer(object):
        Raster = 0
        Timeseries = 1

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        uic.loadUi(join(ui.path, 'axiswidget.ui'), self)

        self.ui = _Ui(self)
        self._setIcons()
        self._initWidgets()
        self._connectSignals()
        self._mode = self.Mode.Undefined

    def _initWidgets(self):
        self.ui.layer().setCurrentIndex(0)
        self.ui.layer().layerChanged.connect(self.ui.band().setLayer)
        if rtm.rtmInstalled:
            self.ui.layer().layerChanged.connect(self.ui.date().setLayer)
            self.ui.layer().layerChanged.connect(self.ui.name().setLayer)
        else:
            self.ui.modeRaster().hide()
            self.ui.modeTimeseries().hide()

    def initMode(self, mode):

        if mode == self.Mode.Band:
            hiddenWidgets = [self.ui.updateDate(), self.ui.date(), self.ui.name()]
            self.ui.updateRange().toggled.connect(self.ui.min().setDisabled)
            self.ui.updateRange().toggled.connect(self.ui.max().setDisabled)
            self.ui.updateBins().toggled.connect(self.ui.bins().setDisabled)
            self.ui.modeTimeseries().toggled.connect(self.ui.date().setVisible)
            self.ui.modeTimeseries().toggled.connect(self.ui.name().setVisible)
            self.ui.modeTimeseries().toggled.connect(self.ui.updateDate().setVisible)
            self.ui.modeRaster().toggled.connect(self.ui.band().setVisible)
        elif mode == self.Mode.SpectralProfile:
            hiddenWidgets = [self.ui.updateDate(), self.ui.date(), self.ui.name(), self.ui.band(),
                             self.ui.updateRange(), self.ui.min(), self.ui.max(),
                             self.ui.updateBins(), self.ui.bins()]
            self.ui.modeTimeseries().toggled.connect(self.ui.date().setVisible)
            self.ui.modeTimeseries().toggled.connect(self.ui.updateDate().setVisible)
        elif mode == self.Mode.TemporalProfile:
            hiddenWidgets = [self.ui.updateDate(), self.ui.date(), self.ui.band(),
                             self.ui.updateRange(), self.ui.min(), self.ui.max(),
                             self.ui.updateBins(), self.ui.bins(),
                             self.ui.modeRaster(), self.ui.modeTimeseries()]
            self.ui.modeTimeseries().setChecked(True)
            self.ui.modeRaster().setChecked(False)
            self.ui.modeTimeseries().toggled.connect(self.ui.date().setVisible)
            self.ui.modeTimeseries().toggled.connect(self.ui.updateDate().setVisible)
        else:
            assert 0

        hiddenWidgets.append(self.ui.x())
        hiddenWidgets.append(self.ui.y())

        for w in hiddenWidgets:
            w.hide()
        self._mode = mode

    def _connectSignals(self):
        self.ui.layer().layerChanged.connect(self.onLayerChanged)
        self.ui.band().currentIndexChanged.connect(lambda index: self.sigAxisChanged.emit(self))
        self.ui.date().currentIndexChanged.connect(lambda index: self.sigAxisChanged.emit(self))
        self.ui.name().currentIndexChanged.connect(lambda index: self.sigAxisChanged.emit(self))
        self.ui.modeRaster().toggled.connect(lambda bool: self.sigAxisChanged.emit(self) if bool else None)
        self.ui.modeTimeseries().toggled.connect(lambda bool: self.sigAxisChanged.emit(self) if bool else None)

        self.ui.x().valueChanged.connect(lambda value: self.sigLocationChanged.emit())
        self.ui.y().valueChanged.connect(lambda value: self.sigLocationChanged.emit())

    def _setIcons(self):
        self.ui.modeRaster().setIcon(QIcon(join(ui.path, 'icon_raster.png')))
        self.ui.modeTimeseries().setIcon(QIcon(join(ui.path, 'icon_timeseries.png')))

    def onLayerChanged(self, layer):
        if isinstance(layer, QgsRasterLayer):
            width, height = layer.width(), layer.height()
            resX, resY = layer.rasterUnitsPerPixelX(), layer.rasterUnitsPerPixelY()
        else:
            width, height = 0, 0
            resX, resY = 0., 0.
        self.ui.x().setMaximum(width - 1)
        self.ui.y().setMaximum(height - 1)
        self.sigAxisChanged.emit(self)

    def setName(self, name):
        self._labelName.setText(name)

    def bins(self, res=None, size=None):
        if self.ui.updateBins().isChecked():
            bins = min(max(math.floor(size * res), 10), 999)
        else:
            bins = self.ui.bins().value()
        return bins

    def setBin(self, bins):
        w = self.ui.bins()
        w.blockSignals(True)
        w.setValue(bins)
        w.blockSignals(False)

    def range(self, dataRange):
        if self.ui.updateRange().isChecked():
           return dataRange
        else:
            min = rdputils.toFloat(self.ui.min().text(), default=0)
            max = rdputils.toFloat(self.ui.max().text(), default=1)
        return min, max

    def setRange(self, range):

        def roundPlotRangeValue(v):
            v = rdputils.toFloat(v)
            if abs(v) < 1:
                v = round(v, 4)
            elif abs(v) < 100:
                v = round(v, 2)
            else:
                v = round(v, 0)
            return v

        for w, v in zip([self.ui.min(), self.ui.max()], range):
            w.blockSignals(True)
            w.setText(str(roundPlotRangeValue(v)))
            w.blockSignals(False)


class _Ui(object):

    def __init__(self, obj):
        self.obj = obj

    def modeRaster(self)->QRadioButton:
        assert isinstance(self.obj._modeRaster, QRadioButton)
        return self.obj._modeRaster

    def modeTimeseries(self):
        assert isinstance(self.obj._modeTimeseries, QRadioButton)
        return self.obj._modeTimeseries

    def layer(self):
        assert isinstance(self.obj._layer, QgsMapLayerComboBox)
        return self.obj._layer

    def band(self):
        assert isinstance(self.obj._band, QgsRasterBandComboBox)
        return self.obj._band

    def x(self):
        assert isinstance(self.obj._x, QSpinBox)
        return self.obj._x

    def y(self):
        assert isinstance(self.obj._y, QSpinBox)
        return self.obj._y

    def updateDate(self):
        assert isinstance(self.obj._updateDate, QToolButton)
        return self.obj._updateDate

    def date(self):
        assert isinstance(self.obj._date, rtm.RtmRasterTimeseriesDateComboBox)
        return self.obj._date

    def name(self):
        assert isinstance(self.obj._name, rtm.RtmRasterTimeseriesBandComboBox)
        return self.obj._name

    def updateRange(self):
        assert isinstance(self.obj._updateRange, QToolButton)
        return self.obj._updateRange

    def min(self):
        assert isinstance(self.obj._min, QLineEdit)
        return self.obj._min

    def max(self):
        assert isinstance(self.obj._max, QLineEdit)
        return self.obj._max

    def updateBins(self):
        assert isinstance(self.obj._updateBins, QToolButton)
        return self.obj._updateBins

    def bins(self):
        assert isinstance(self.obj._bins, QSpinBox)
        return self.obj._bins
