from os.path import join
from qgis.gui import *
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import *

from .. import ui
from .. import rdputils
from .rdpscatterplotwidget import RdpScatterPlotWidget
from .rdpspectralprofileplotwidget import RdpSpectralProfilePlotWidget
from .rdptemporalprofileplotwidget import RdpTemporalProfilePlotWidget

class RdpDockWidget(QgsDockWidget):

    iface = None

    class PlotType(object):
        Undefined = 0
        Scatter = 1
        SpectralProfile = 2
        TemporalProfile = 3

    def __init__(self, parent=None):
        QgsDockWidget.__init__(self, parent)
        RdpScatterPlotWidget.iface = self.iface
        RdpSpectralProfilePlotWidget.iface = self.iface
        RdpTemporalProfilePlotWidget.iface = self.iface
        uic.loadUi(join(ui.path, 'dockwidget.ui'), self)
        self._initUi()
        self._connectSignals()

    def _initUi(self):
        self.ui = _Ui(self)
        self.setWindowTitle('{} (v{})'.format(self.windowTitle(), rdputils.version()))
        self.onPlotTypeChanged(plotType=self.PlotType.Undefined)

    def _connectSignals(self):
        self.ui.refresh().clicked.connect(self.onRefreshClicked)
        self.ui.plotType().currentIndexChanged.connect(self.onPlotTypeChanged)

    def onRefreshClicked(self):
        plotType = self.ui.plotType().currentIndex()
        if plotType == self.PlotType.Undefined:
            pass
        elif plotType == self.PlotType.Scatter:
            self.ui.scatterPlot().resetData()
        elif plotType == self.PlotType.SpectralProfile:
            self.ui.spectralProfilePlot().resetData()
        elif plotType == self.PlotType.TemporalProfile:
            self.ui.spectralProfilePlot().resetData()
        else:
            assert 0

    def onPlotTypeChanged(self, plotType):
        # Turn plotting on for selected plot, and turn it off for all other plots
        plots = {1: self.ui.scatterPlot(), 2: self.ui.spectralProfilePlot(), 3: self.ui.temporalProfilePlot()}
        for i, plot in plots.items():
            plot.ui.showPlot().setChecked(i == plotType)

        if plotType == self.PlotType.SpectralProfile:
            self.ui.spectralProfilePlot().ui.mapTool().clicked.emit()

        if plotType == self.PlotType.TemporalProfile:
            from ..site.rastertimeseriesmanager import rtmInstalled
            if not rtmInstalled:
                from qgis.core import Qgis
                self.ui.temporalProfilePlot().hide()
                self.iface.messageBar().pushMessage('Info', "For Temporal Profile Plots install the RasterTimeseriesManager plugin.",
                                                    level=Qgis.Info, duration=10)
                return

            self.ui.temporalProfilePlot().ui.mapTool().clicked.emit()


class _Ui(object):

    def __init__(self, obj):
        self.obj = obj

    def plotType(self):
        assert isinstance(self.obj._plotType, QComboBox)
        return self.obj._plotType

    def scatterPlot(self):
        assert isinstance(self.obj._scatterPlot, RdpScatterPlotWidget)
        return self.obj._scatterPlot

    def spectralProfilePlot(self):
        assert isinstance(self.obj._spectralProfilePlot, RdpSpectralProfilePlotWidget)
        return self.obj._spectralProfilePlot

    def temporalProfilePlot(self):
        assert isinstance(self.obj._temporalProfilePlot, RdpTemporalProfilePlotWidget)
        return self.obj._temporalProfilePlot

    def refresh(self):
        assert isinstance(self.obj._refresh, QToolButton)
        return self.obj._refresh
