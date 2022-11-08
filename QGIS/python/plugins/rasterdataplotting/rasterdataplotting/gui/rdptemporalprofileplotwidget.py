from qgis.PyQt.QtCore import *

from .rdpprofileplotwidgetbase import RdpProfilePlotWidgetBase
from .rdpaxiswidget import RdpAxisWidget

debug = True


class RdpTemporalProfilePlotWidget(RdpProfilePlotWidgetBase):
    sigFirstProfileChanged = pyqtSignal(object)

    def axisMode(self):
        return RdpAxisWidget.Mode.TemporalProfile

    def readAndPlotData(self):
        RdpProfilePlotWidgetBase.readAndPlotData(self)

        if len(self.dataHandler._plotDataItems) > 0:
            datas = list()
            for plotDataItem in self.dataHandler._plotDataItems:
                datas.append(plotDataItem.getData())
            from rasterdataplotting import rdpInterface

            try:
                temporalProfilePlot = rdpInterface().ui.ui.temporalProfilePlot()
            except AttributeError:
                return
            temporalProfilePlot.sigFirstProfileChanged.emit(datas)
