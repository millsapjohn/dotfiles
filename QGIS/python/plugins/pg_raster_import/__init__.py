# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PGRasterImport
                                 A QGIS plugin
 Import Raster to PgRaster
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2021-06-24
        copyright            : (C) 2021 by Dr. Horst Duester / Sourcepols
        email                : horst.duester@sourcepole.ch
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load PGRasterImport class from file PGRasterImport.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .pgraster_import import PGRasterImport
    return PGRasterImport(iface)
