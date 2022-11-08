from osgeo import gdal
from .rasterdataplotting.plugin import RdpPlugin

gdal.SetConfigOption('GDAL_VRT_ENABLE_PYTHON', 'YES')


def classFactory(iface):
    return RdpPlugin(iface)


def rdpInterface():
    from rasterdataplotting.rasterdataplotting.core.rdpinterface import RdpInterface
    return RdpInterface.instance()
