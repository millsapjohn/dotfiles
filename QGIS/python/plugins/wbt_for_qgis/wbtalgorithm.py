# -*- coding: utf-8 -*-

"""
***************************************************************************
    wbtalgorithm.py
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
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterMapLayer,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingOutputHtml,
                       QgsProcessingOutputFile,
                       QgsMapLayerType
                      )
from processing.core.parameters import getParameterFromString

from wbt_for_qgis import utils

pluginPath = os.path.dirname(__file__)


class WbtAlgorithm(QgsProcessingAlgorithm):

    def __init__(self, descriptionFile):
        super().__init__()

        self.descriptionFile = descriptionFile
        self._name = ''
        self._displayName = ''
        self._group = ''
        self._groupId = ''
        self._shortHelp = ''
        self._helpUrl = ''

        self.params = []

        self.defineCharacteristicsFromFile()

    def createInstance(self):
        return self.__class__(self.descriptionFile)

    def name(self):
        return self._name

    def displayName(self):
        return self._displayName

    def group(self):
        return self._group

    def groupId(self):
        return self._groupId

    def shortHelpString(self):
        return self._shortHelp

    def helpUrl(self):
        return self._helpUrl

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'icons', 'whiteboxtools.svg'))

    def tr(self, text):
        return QCoreApplication.translate(self.__class__.__name__, text)

    def initAlgorithm(self, config=None):
        for p in self.params:
            self.addParameter(p, True)

    def defineCharacteristicsFromFile(self):
        with open(self.descriptionFile) as lines:
            line = lines.readline().strip('\n').strip()
            self._name = line

            line = lines.readline().strip('\n').strip()
            self._displayName = line

            line = lines.readline().strip('\n').strip()
            self._group = line

            line = lines.readline().strip('\n').strip()
            self._groupId = line

            line = lines.readline().strip('\n').strip()
            self._shortHelp = line

            line = lines.readline().strip('\n').strip()
            self._helpUrl = line

            line = lines.readline().strip('\n').strip()
            while line != '':
                self.params.append(getParameterFromString(line, 'WbtAlgorithm'))
                line = lines.readline().strip('\n').strip()

    def processAlgorithm(self, parameters, context, feedback):
        arguments = ['"{}"'.format(utils.wbtExecutable()),
                     '-v',
                     '--run={}'.format(self.name())
                    ]

        for param in self.parameterDefinitions():
            if param.isDestination():
                continue

            if param.name() not in parameters or parameters[param.name()] is None:
                continue

            if isinstance(param, QgsProcessingParameterMapLayer):
                layer = self.parameterAsLayer(parameters, param.name(), context)
                if layer is not None:
                    filePath = layer.source()
                    # sometimes both raster and vector layers are accepted
                    if layer.type() == QgsMapLayerType.VectorLayer:
                        filePath = self.parameterAsCompatibleSourceLayerPath(parameters, param.name(), context, ['shp'], 'shp', feedback=feedback)
                    arguments.append('--{}="{}"'.format(param.name(), os.path.normpath(filePath)))
            if isinstance(param, QgsProcessingParameterRasterLayer):
                layer = self.parameterAsRasterLayer(parameters, param.name(), context)
                if layer is not None:
                    arguments.append('--{}="{}"'.format(param.name(), os.path.normpath(layer.source())))
            if isinstance(param, QgsProcessingParameterFeatureSource):
                filePath = self.parameterAsCompatibleSourceLayerPath(parameters, param.name(), context, ['shp'], 'shp', feedback=feedback)
                arguments.append('--{}="{}"'.format(param.name(), os.path.normpath(filePath)))
            elif isinstance(param, QgsProcessingParameterMultipleLayers):
                layers = self.parameterAsLayerList(parameters, param.name(), context)
                if layers is None or len(layers) == 0:
                    continue
                files = []
                if param.layerType() == QgsProcessing.TypeFile:
                    files = [os.path.normpath(layer.source()) for layer in layers]
                elif param.layerType() == QgsProcessing.TypeRaster:
                    files = [os.path.normpath(layer.source()) for layer in layers]
                else:
                    files = []
                    for i, layer in enumerate(layers):
                        tmp  = QgsProcessingUtils.convertToCompatibleFormat(layer, False, 'exported-{}'.format(i), ['shp'], 'shp', context, feedback)
                        files.append(os.path.normpath(tmp))
                arguments.append('--{}="{}"'.format(param.name(), ','.join(files)))
            elif isinstance(param, QgsProcessingParameterBoolean):
                arguments.append('--{}="{}"'.format(param.name(), self.parameterAsBool(parameters, param.name(), context)))
            elif isinstance(param, QgsProcessingParameterNumber):
                if param.dataType() == QgsProcessingParameterNumber.Integer:
                    arguments.append('--{}={}'.format(param.name(), self.parameterAsInt(parameters, param.name(), context)))
                else:
                    arguments.append('--{}={}'.format(param.name(), self.parameterAsDouble(parameters, param.name(), context)))
            elif isinstance(param, QgsProcessingParameterEnum):
                idx = self.parameterAsEnum(parameters, param.name(), context)
                arguments.append('--{}="{}"'.format(param.name(), param.options()[idx]))
            elif isinstance(param, (QgsProcessingParameterFile)):
                arguments.append('--{}="{}"'.format(param.name(), os.path.normpath(self.parameterAsFile(parameters, param.name(), context))))
            elif isinstance(param, (QgsProcessingParameterString)):
                arguments.append('--{}="{}"'.format(param.name(), self.parameterAsString(parameters, param.name(), context)))

        for out in self.destinationParameterDefinitions():
            if param.name() not in parameters or parameters[param.name()] is None:
                continue

            if isinstance(out, QgsProcessingParameterRasterDestination):
                arguments.append('--{}="{}"'.format(out.name(), os.path.normpath(self.parameterAsOutputLayer(parameters, out.name(), context))))
            if isinstance(out, QgsProcessingParameterVectorDestination):
                arguments.append('--{}="{}"'.format(out.name(), os.path.normpath(self.parameterAsOutputLayer(parameters, out.name(), context))))
            elif isinstance(out, QgsProcessingParameterFileDestination):
                arguments.append('--{}="{}"'.format(out.name(), os.path.normpath(self.parameterAsFileOutput(parameters, out.name(), context))))

        utils.execute(arguments, feedback)

        results = {}
        for output in self.outputDefinitions():
            outputName = output.name()
            if outputName in parameters:
                results[outputName] = parameters[outputName]

        return results
