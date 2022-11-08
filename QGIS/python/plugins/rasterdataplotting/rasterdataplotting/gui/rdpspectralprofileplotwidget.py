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
from .rdpprofileplotwidgetbase import RdpProfilePlotWidgetBase
from .rdpaxiswidget import RdpAxisWidget

debug = True

class RdpSpectralProfilePlotWidget(RdpProfilePlotWidgetBase):
    pass

    def axisMode(self):
        return RdpAxisWidget.Mode.SpectralProfile
