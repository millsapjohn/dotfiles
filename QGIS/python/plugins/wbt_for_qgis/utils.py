# -*- coding: utf-8 -*-

"""
***************************************************************************
    utils.py
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
import re
import subprocess

from qgis.PyQt.QtCore import QProcess
from qgis.core import (Qgis,
                       QgsMessageLog,
                       QgsRunProcess,
                       QgsBlockingProcess,
                       QgsProcessingFeedback,
                       QgsProcessingException
                      )
from processing.core.ProcessingConfig import ProcessingConfig

progressRegex = re.compile('\d+')

WBT_EXECUTABLE = 'WBT_EXECUTABLE'


def wbtExecutable():
    filePath = ProcessingConfig.getSetting(WBT_EXECUTABLE)
    return filePath if filePath is not None else 'whitebox_tools'


def descriptionsPath():
    return os.path.normpath(os.path.join(os.path.dirname(__file__), 'descriptions'))


def execute(commands, feedback=None):
    if feedback is None:
        feedback = QgsProcessingFeedback()

    fused_command = ' '.join([str(c) for c in commands])
    QgsMessageLog.logMessage(fused_command, 'Processing', Qgis.Info)
    feedback.pushInfo('WhiteboxTools command:')
    feedback.pushCommandInfo(fused_command)
    feedback.pushInfo('WhiteboxTools output:')

    def onStdOut(ba):
        val = ba.data().decode('utf-8')
        if '%' in val:
            onStdOut.progress = int(progressRegex.search(val).group(0))
            feedback.setProgress(onStdOut.progress)
        else:
            onStdOut.buffer += val

        if onStdOut.buffer.endswith(('\n', '\r')):
            feedback.pushConsoleInfo(onStdOut.buffer.rstrip())
            onStdOut.buffer = ''

    onStdOut.progress = 0
    onStdOut.buffer = ''

    def onStdErr(ba):
        val = ba.data().decode('utf-8')
        onStdErr.buffer += val

        if onStdErr.buffer.endswith(('\n', '\r')):
            feedback.reportError(onStdErr.buffer.rstrip())
            onStdErr.buffer = ''

    onStdErr.buffer = ''

    command, *arguments = QgsRunProcess.splitCommand(fused_command)
    proc = QgsBlockingProcess(command, arguments)
    proc.setStdOutHandler(onStdOut)
    proc.setStdErrHandler(onStdErr)

    res = proc.run(feedback)
    if feedback.isCanceled() and res != 0:
        feedback.pushInfo('Process was canceled and did not complete.')
    elif not feedback.isCanceled() and proc.exitStatus() == QProcess.CrashExit:
        raise QgsProcessingException('Process was unexpectedly terminated.')
    elif res == 0:
        feedback.pushInfo('Process completed successfully.')
    elif proc.processError() == QProcess.FailedToStart:
        raise QgsProcessingException('Process "{}" failed to start. Either "{}" is missing, or you may have insufficient permissions to run the program.'.format(command, command))
    else:
        feedback.reportError('Process returned error code {}'.format(res))
