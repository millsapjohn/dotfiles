# -*- coding: utf-8 -*-

"""
***************************************************************************
    wbtprovider.py
    ---------------------
    Date                 : December 2017
    Copyright            : (C) 2017-2020 by Alexander Bruy
    Email                : alexander dot bruy at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Alexander Bruy'
__date__ = 'December 2017'
__copyright__ = '(C) 2017-2020, Alexander Bruy'


import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import Qgis, QgsProcessingProvider, QgsMessageLog

from processing.core.ProcessingConfig import ProcessingConfig, Setting

from wbt_for_qgis.wbtalgorithm import WbtAlgorithm
from wbt_for_qgis import utils
from wbt_for_qgis import wbtdescriptions

pluginPath = os.path.dirname(__file__)


class WbtProvider(QgsProcessingProvider):

    def __init__(self):
        super().__init__()
        self.algs = []

    def id(self):
        return 'wbt'

    def name(self):
        return 'WhiteboxTools'

    def longName(self):
        return 'WhiteboxTools'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'icons', 'whiteboxtools.svg'))

    def load(self):
        ProcessingConfig.settingIcons[self.name()] = self.icon()
        ProcessingConfig.addSetting(Setting(self.name(),
                                            utils.WBT_EXECUTABLE,
                                            self.tr('WhiteboxTools executable'),
                                            utils.wbtExecutable(),
                                            valuetype=Setting.FILE))
        ProcessingConfig.readSettings()
        self.refreshAlgorithms()
        return True

    def unload(self):
        ProcessingConfig.removeSetting(utils.WBT_EXECUTABLE)

    def defaultVectorFileExtension(self, hasGeometry=True):
        return 'shp'

    def defaultRasterFileExtension(self):
        return 'tif'

    def supportedOutputRasterLayerExtensions(self):
        return ['tif', 'flt', 'sdat', 'rdc', 'dep']

    def supportsNonFileBasedOutput(self):
        return False

    def loadAlgorithms(self):
        self.algs = []
        folder = utils.descriptionsPath()
        wbtdescriptions.createDescriptions()
        for descriptionFile in os.listdir(folder):
            if descriptionFile.endswith('txt'):
                try:
                    alg = WbtAlgorithm(os.path.join(folder, descriptionFile))
                    if alg.name().strip() != '':
                        self.algs.append(alg)
                    else:
                        QgsMessageLog.logMessage(self.tr('Could not load WhiteboxTools algorithm from file "{}".'.format(descriptionFile)),
                                                 self.tr('Processing'), Qgis.Critical)
                except Exception as e:
                    QgsMessageLog.logMessage(self.tr('Could not load WhiteboxTools algorithm from file "{}".\n{}'.format(descriptionFile, str(e))),
                                             self.tr('Processing'), Qgis.Critical)

        for a in self.algs:
            self.addAlgorithm(a)

    def tr(self, string, context=''):
        return QCoreApplication.translate(self.__class__.__name__, string)
