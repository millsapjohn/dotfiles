from __future__ import absolute_import
from qgis.gui import QgisInterface, QtCore

from .core.rdpinterface import RdpInterface


class RdpPlugin(object):

    def __init__(self, iface):
        assert isinstance(iface, QgisInterface)
        self.iface = iface

    def initGui(self):
        self.rdpInterface = RdpInterface(self.iface)
        self.rdpInterface.show()
        self.iface.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.rdpInterface.ui)

    def unload(self):
        self.rdpInterface.unloadPlugin()
        self.iface.removeDockWidget(self.rdpInterface.ui)
