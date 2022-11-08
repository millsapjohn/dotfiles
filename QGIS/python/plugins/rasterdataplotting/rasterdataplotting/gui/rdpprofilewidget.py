from os.path import join
import math
import numpy as np
from qgis._core import QgsPointXY
from qgis.gui import *
from qgis.core import *
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from ..site import pyqtgraph as pg
from .. import ui
from .rdpaxiswidget import RdpAxisWidget
from ..site import rastertimeseriesmanager as rtm


debug = True

class RdpProfileWidget(QWidget):

    sigLocationChanged = pyqtSignal()

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        uic.loadUi(join(ui.path, 'profilewidget.ui'), self)
        self.ui = _Ui(self)
        self._initUi()
        self._connectSignals()

    def _initUi(self):
        pass

    def _connectSignals(self):
        self.ui.axis().sigLocationChanged.connect(lambda: self.sigLocationChanged.emit())


class _Ui(object):

    def __init__(self, obj):
        self.obj = obj

    def show(self):
        assert isinstance(self.obj._show, QToolButton)
        return self.obj._show

    def axis(self):
        assert isinstance(self.obj._axis, RdpAxisWidget)
        return self.obj._axis

    def scale(self):
        assert isinstance(self.obj._scale, QLineEdit)
        return self.obj._scale

    def color(self):
        assert isinstance(self.obj._color, QgsColorButton)
        return self.obj._color


