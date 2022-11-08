# -*- coding: utf-8 -*-

"""
***************************************************************************
    whiteboxDescriptions.py
    ---------------------
    Date                 : December 2017
    Copyright            : (C) 2017 by Alexander Bruy
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

__author__ = 'Alexander Bruy and John Lindsay'
__date__ = 'December 2017'
__copyright__ = '(C) 2017, Alexander Bruy and John Lindsay'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'


import re
import os
import json
import argparse
import tempfile
import subprocess

from wbt_for_qgis import utils

HELP_URL_BASE = 'https://www.whiteboxgeo.com/manual/wbt_book/available_tools'

FIRST_CAP = re.compile('(.)([A-Z][a-z]+)')
ALL_CAP = re.compile('([a-z0-9])([A-Z])')


def whiteboxTools():
    tools = None
    wb = utils.wbtExecutable()
    if wb == '':
        wb = 'whitebox_tools'

    command = ['{} --listtools'.format(wb)]
    with subprocess.Popen(command,
                          shell=True,
                          stdout=subprocess.PIPE,
                          stdin=subprocess.DEVNULL,
                          stderr=subprocess.STDOUT,
                          universal_newlines=True) as proc:
        try:
            tools = dict()
            for line in proc.stdout:
                if 'Available Tools' in line:
                    continue
                elif line == '\n':
                    continue
                t = line.strip().split(':')
                toolName = t[0].strip()
                toolHelp = t[1].strip()
                tools[toolName] = toolHelp[:-1]
        except Exception as e:
            print('Can not get list of the available tools:\n{}'.format(str(e)))
            return None

        return tools


def createDescriptions(descriptionPath=None):
    tools = whiteboxTools()
    wb = utils.wbtExecutable()
    if wb == '':
        wb = 'whitebox_tools'

    if descriptionPath is None:
        descriptionPath = utils.descriptionsPath()

    # how many files are in the folder?
    num_description_files = 0
    for descriptionFile in os.listdir(descriptionPath):
            if descriptionFile.endswith('txt'):
                num_description_files += 1

    if tools is not None and len(tools) > num_description_files:
        count = 0
        for tool, shortHelp in tools.items():
            group = 'Whitebox Tools'
            helpPageUrl = HELP_URL_BASE
            command = ['{} --toolbox="{}"'.format(wb, tool)]
            with subprocess.Popen(command,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stdin=subprocess.DEVNULL,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True) as proc:
                try:
                    for line in proc.stdout:
                        t = line.strip()
                        group = t if '/' not in t else t.replace('/', ' - ')
                        helpPageUrl = helpUrl(tool, t)
                except Exception as e:
                    print('Can not get toolbox for the tool {}:\n{}'.format(tool, str(e)))
                    continue

            params = ''
            command = ['{} --toolparameters="{}"'.format(wb, tool)]
            with subprocess.Popen(command,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stdin=subprocess.DEVNULL,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True) as proc:
                try:
                    params = ''.join(proc.stdout)
                except Exception as e:
                    print('Can not get parameters for tool {}:\n{}'.format(tool, str(e)))
                    continue

            j = json.loads(params)

            error = False
            params = []

            # collect inputs
            for p in j['parameters']:
                parameterType = p['parameter_type']
                if 'NewFile' in parameterType:
                    continue

                param = _parameterDefinitionFromDict(p)
                if param:
                    params.append(param)
                else:
                    print('{} - failed to process parameter:\n{}'.format(tool, p))
                    error = True
                    break

            # collect outputs
            for p in j['parameters']:
                parameterType = p['parameter_type']
                if 'NewFile' not in parameterType:
                    continue

                param = _outputDefinitionFromDict(p)
                if param:
                    params.append(param)
                else:
                    print('{} - failed to process parameter:\n{}'.format(tool, p))
                    error = True
                    break

            if not error:
                count += 1
                with open(os.path.join(descriptionPath, '{}.txt'.format(tool)), 'w') as f:
                    f.write('{}\n'.format(tool))
                    t = re.sub('(?!^)([A-Z][a-z]+)', r' \1', tool)
                    if t[1] == ' ':
                        tool = t.replace(' ', '', 1)
                    f.write('{}\n'.format(tool))
                    f.write('{}\n'.format(group))
                    f.write('{}\n'.format(''.join(group.replace('-', '').split()).lower()))
                    f.write('{}\n'.format(shortHelp))
                    f.write('{}\n'.format(helpPageUrl))
                    f.write('{}\n'.format('\n'.join(params)))

        print('\n{} out of {} processed'.format(count, len(tools)))


def _parameterDefinitionFromDict(param):
    parameterType = param['parameter_type']

    name = param['flags'][0].lstrip('-') if len(param['flags']) == 1 else param['flags'][1].lstrip('-')
    description = param['name']
    optional = param['optional']

    # input parameters
    if 'ExistingFileOrFloat' in parameterType or 'ExistingFile' in parameterType:
        if 'ExistingFileOrFloat' in parameterType:
            dataType = param['parameter_type']['ExistingFileOrFloat']
        elif 'ExistingFile' in parameterType:
            dataType = param['parameter_type']['ExistingFile']
            if isinstance(dataType, dict):
                dataType = list(dataType.keys())[0]
        else:
            return None

        if dataType == 'Raster':
            return 'QgsProcessingParameterRasterLayer|{}|{}|None|{}'.format(name, description, optional)
        elif dataType == 'Vector':
            geometryType = param['parameter_type']['ExistingFile'][dataType]
            if geometryType == 'Point':
                return 'QgsProcessingParameterFeatureSource|{}|{}|QgsProcessing.TypeVectorPoint|None|{}'.format(name, description, optional)
            elif geometryType == 'Line':
                return 'QgsProcessingParameterFeatureSource|{}|{}|QgsProcessing.TypeVectorLine|None|{}'.format(name, description, optional)
            elif geometryType == 'Polygon':
                return 'QgsProcessingParameterFeatureSource|{}|{}|QgsProcessing.TypeVectorPolygon|None|{}'.format(name, description, optional)
            elif geometryType == 'LineOrPolygon':
                return 'QgsProcessingParameterFeatureSource|{}|{}|QgsProcessing.TypeVectorPolygon;QgsProcessing.TypeVectorLine|None|{}'.format(name, description, optional)
            elif geometryType == 'Any':
                return 'QgsProcessingParameterFeatureSource|{}|{}|QgsProcessing.TypeVectorAnyGeometry|None|{}'.format(name, description, optional)
            else:
                return None
        elif dataType == 'Csv':
            return 'QgsProcessingParameterFile|{}|{}|QgsProcessingParameterFile.File|csv|None|{}'.format(name, description, optional)
        elif dataType == 'Text':
            return 'QgsProcessingParameterFile|{}|{}|QgsProcessingParameterFile.File|txt|None|{}'.format(name, description, optional)
        elif dataType == 'HTML':
            return 'QgsProcessingParameterFile|{}|{}|QgsProcessingParameterFile.File|html|None|{}'.format(name, description, optional)
        elif dataType == 'Lidar':
            return 'QgsProcessingParameterFile|{}|{}|QgsProcessingParameterFile.File|None|None|{}|Lidar Files (*.las *.laz *.zlidar)'.format(name, description, optional)
        elif dataType == 'RasterAndVector':
            fileType = param['parameter_type']['ExistingFile'][dataType]
            dataTypes = ['QgsProcessing.TypeRaster']
            if fileType == 'Point':
                dataTypes.append('QgsProcessing.TypeVectorPoint')
            elif fileType == 'Any':
                dataTypes.append('QgsProcessing.TypeVectorAnyGeometry')
            else:
                return None

            return 'QgsProcessingParameterMapLayer|{}|{}|None|{}|{}'.format(name, description, optional, ';'.join(dataTypes))
        else:
            return None
    elif 'FileList' in parameterType:
        dataType = param['parameter_type']['FileList']
        if isinstance(dataType, dict):
            dataType = list(dataType.keys())[0]

        if dataType == 'Raster':
            return 'QgsProcessingParameterMultipleLayers|{}|{}|QgsProcessing.TypeRaster|None|False'.format(name, description, optional)
        elif dataType == 'Vector':
            geometryType = param['parameter_type']['FileList'][dataType]
            if geometryType == 'Point':
                return 'QgsProcessingParameterMultipleLayers|{}|{}|QgsProcessing.TypeVectorPoint|None|False'.format(name, description, optional)
            elif geometryType == 'Line':
                return 'QgsProcessingParameterMultipleLayers|{}|{}|QgsProcessing.TypeVectorLine|None|False'.format(name, description, optional)
            elif geometryType == 'Polygon':
                return 'QgsProcessingParameterMultipleLayers|{}|{}|QgsProcessing.TypeVectorPolygon|None|False'.format(name, description, optional)
            elif geometryType == 'Any':
                return 'QgsProcessingParameterMultipleLayers|{}|{}|QgsProcessing.TypeVectorAnyGeometry|None|False'.format(name, description, optional)
            else:
                return None
        elif dataType in ('Lidar'):
            return 'QgsProcessingParameterMultipleLayers|{}|{}|QgsProcessing.TypePointCloud|None|False'.format(name, description, optional)
        elif dataType in ('Csv'):
            return 'QgsProcessingParameterMultipleLayers|{}|{}|QgsProcessing.TypeFile|None|False'.format(name, description, optional)
        else:
            return None
    elif 'OptionList' in parameterType:
        options = [v.strip('"') for v in param['parameter_type']['OptionList']]
        try:
            defaultValue = options.index(param['default_value'])
        except ValueError:
            options.append(param['default_value'].strip('"'))
            defaultValue = options.index(param['default_value'])
        return 'QgsProcessingParameterEnum|{}|{}|{}|False|{}|{}'.format(name, description, ';'.join(options), defaultValue, optional)
    elif 'Boolean' in parameterType:
        defaultValue = True if param['default_value'] != None and param['default_value'].lower() == 'true' else False
        return 'QgsProcessingParameterBoolean|{}|{}|{}|{}'.format(name, description, defaultValue, optional)
    elif 'Float' in parameterType or 'Integer' in parameterType:
        dataType = param['parameter_type']
        defaultValue = param['default_value']
        if defaultValue == None or defaultValue == '':
            defaultValue = "None"
            
        if dataType == 'Integer':
            return 'QgsProcessingParameterNumber|{}|{}|QgsProcessingParameterNumber.Integer|{}|{}|None|None'.format(name, description, defaultValue, optional)
        else:
            return 'QgsProcessingParameterNumber|{}|{}|QgsProcessingParameterNumber.Double|{}|{}|None|None'.format(name, description, defaultValue, optional)
    elif 'String' in parameterType:
        defaultValue = param['default_value']
        if defaultValue == None or defaultValue == '':
            defaultValue = "None"
        return 'QgsProcessingParameterString|{}|{}|{}|False|{}'.format(name, description, defaultValue, optional)
    elif 'VectorAttributeField' in parameterType:
        defaultValue = param['default_value']
        dataType = param['parameter_type']['VectorAttributeField'][0]
        parent = param['parameter_type']['VectorAttributeField'][1].lstrip('-')
        if dataType == 'Number':
            dataType = 'QgsProcessingParameterField.Number'
        else:
            dataType = 'QgsProcessingParameterField.Any'
        return 'QgsProcessingParameterField|{}|{}|{}|{}|QgsProcessingParameterField.Any|False|{}'.format(name, description, defaultValue, parent, dataType, optional)
    elif 'Directory' in parameterType:
        return 'QgsProcessingParameterFile|{}|{}|QgsProcessingParameterFile.Folder|None|None|{}'.format(name, description, optional)
    else:
        return None


def _outputDefinitionFromDict(param):
    parameterType = param['parameter_type']

    name = param['flags'][0].lstrip('-') if len(param['flags']) == 1 else param['flags'][1].lstrip('-')
    description = param['name']
    optional = param['optional']

    dataType = param['parameter_type']['NewFile']
    if isinstance(dataType, dict):
        dataType = list(dataType.keys())[0]

    if dataType == 'Raster':
        return 'QgsProcessingParameterRasterDestination|{}|{}|None|{}'.format(name, description, optional)
    elif dataType == 'Vector':
        geometryType = param['parameter_type']['NewFile'][dataType]
        if geometryType == 'Point':
            return 'QgsProcessingParameterVectorDestination|{}|{}|QgsProcessing.TypeVectorPoint|None|{}'.format(name, description, optional)
        elif geometryType == 'Line':
            return 'QgsProcessingParameterVectorDestination|{}|{}|QgsProcessing.TypeVectorLine|None|{}'.format(name, description, optional)
        elif geometryType == 'Polygon':
            return 'QgsProcessingParameterVectorDestination|{}|{}|QgsProcessing.TypeVectorPolygon|None|{}'.format(name, description, optional)
        elif geometryType == 'Any':
            return 'QgsProcessingParameterVectorDestination|{}|{}|QgsProcessing.TypeVectorAnyGeometry|None|{}'.format(name, description, optional)
        else:
            return None
    elif dataType == 'Html':
        return 'QgsProcessingParameterFileDestination|{}|{}|HTML files (*.html *.HTML)|None|{}'.format(name, description, optional)
    elif dataType == 'Lidar':
        return 'QgsProcessingParameterFileDestination|{}|{}|LiDAR files (*.las *.laz *.zlidar)|None|{}'.format(name, description, optional)
    elif dataType == 'Csv':
        return 'QgsProcessingParameterFileDestination|{}|{}|CSV files (*.csv *.CSV)|None|{}'.format(name, description, optional)
    else:
        return None

def helpUrl(tool, group):
    tmp = FIRST_CAP.sub(r'\1_\2', group.replace('/', '').replace(' ', ''))
    groupName = ALL_CAP.sub(r'\1_\2', tmp).lower()
    if groupName == 'li_dar_tools':
        groupName = 'lidar_tools'
    return '{}/{}.html#{}'.format(HELP_URL_BASE, groupName, tool)


if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='Generate Whitebox Tools descriptions for Processing.')
    # parser.add_argument('directory', metavar='DIRECTORY', nargs='?', default=tempfile.gettempdir(), help='output directory')
    # args = parser.parse_args()
    
    # createDescriptions(args.directory)
    createDescriptions()
