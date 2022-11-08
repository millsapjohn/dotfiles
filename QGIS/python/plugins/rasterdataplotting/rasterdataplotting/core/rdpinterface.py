from collections import namedtuple
import traceback
import numpy as np
import math
from qgis.core import *
from os.path import join, dirname
from qgis.gui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from .. import rdputils
from ..site import pyqtgraph as pg
from ..gui.rdpdockwidget import RdpDockWidget


debug = True

class RdpInterface(QObject):

    INSTANCE = None
    pluginName = 'Raster Data Plotting'
    pluginId = pluginName.replace(' ', '')

    def __init__(self, iface, parent=None):

        if self.INSTANCE is not None:
            raise Exception('{} already initialized.'.format(self.pluginName))
        else:
            RdpInterface.INSTANCE = self

        QObject.__init__(self, parent)
        assert isinstance(iface, QgisInterface)
        self.iface = iface
        self._initUi()
        self.integratePlugin()

    def _initUi(self):
        RdpDockWidget.iface = self.iface
        self.ui = RdpDockWidget(parent=self.parent())
        self.ui.setWindowIcon(self.icon())

    def integratePlugin(self):
        if isinstance(self.iface, QgisInterface):
            self.action = QAction(self.icon(), self.pluginId, self.iface.mainWindow())
            self.action.triggered.connect(self.toggleUiVisibility)
            self.iface.addToolBarIcon(self.action)

    def unloadPlugin(self):
        self.ui.close()
        self.iface.removeToolBarIcon(self.action)

    @classmethod
    def instance(cls):
        if cls.INSTANCE is None:
            raise Exception('{} not initialized.'.format(cls.pluginName))

        assert isinstance(cls.INSTANCE, RdpInterface)
        return cls.INSTANCE

    def pluginFolder(self):
        return join(dirname(__file__), '..', '..')

    def icon(self):
        return QIcon(join(self.pluginFolder(), 'icon.png'))

    def toggleUiVisibility(self):
        self.ui.setVisible(not self.ui.isVisible())

    def show(self):
        self.ui.show()
