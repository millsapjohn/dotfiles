# -*- coding: utf-8 -*-

"""
***************************************************************************
    __init__.py
    ---------------------
    Date                 : December 2017
    Copyright            : (C) 2017-2022 by John Lindsay and Alexander Bruy
    Email                : support@whiteboxgeo.com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'John Lindsay and Alexander Bruy'
__date__ = 'December 2017'
__copyright__ = '(C) 2017-2022, John Lindsay and Alexander Bruy'


from wbt_for_qgis.plugin import WbtPlugin


def classFactory(iface):
    return WbtPlugin()
