# -*- coding: utf-8 -*-
'''
/**************************************************************************************************************************
 SemiAutomaticClassificationPlugin

 The Semi-Automatic Classification Plugin for QGIS allows for the supervised classification of remote sensing images, 
 providing tools for the download, the preprocessing and postprocessing of images.

							 -------------------
		begin				: 2012-12-29
		copyright		: (C) 2012-2021 by Luca Congedo
		email				: ing.congedoluca@gmail.com
**************************************************************************************************************************/
 
/**************************************************************************************************************************
 *
 * This file is part of Semi-Automatic Classification Plugin
 * 
 * Semi-Automatic Classification Plugin is free software: you can redistribute it and/or modify it under 
 * the terms of the GNU General Public License as published by the Free Software Foundation, 
 * version 3 of the License.
 * 
 * Semi-Automatic Classification Plugin is distributed in the hope that it will be useful, 
 * but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or 
 * FITNESS FOR A PARTICULAR PURPOSE. 
 * See the GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License along with 
 * Semi-Automatic Classification Plugin. If not, see <http://www.gnu.org/licenses/>. 
 * 
**************************************************************************************************************************/

'''



cfg = __import__(str(__name__).split('.')[0] + '.core.config', fromlist=[''])

class ErosionRaster:

	def __init__(self):
		pass
		
	# value text changed
	def textChanged(self):		
		self.checkValueList()
		
	# check value list
	def checkValueList(self):
		try:
			# class value list
			valueList = cfg.utls.textToValueList(cfg.ui.erosion_classes_lineEdit.text())
			cfg.ui.erosion_classes_lineEdit.setStyleSheet('color : green')
			# logger
			cfg.utls.logCondition(str(__name__) + '-' + str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode())
		except Exception as err:
			cfg.ui.erosion_classes_lineEdit.setStyleSheet('color : red')
			valueList = []
			# logger
			cfg.utls.logCondition(str(__name__) + '-' + (cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), ' ERROR exception: ' + str(err))
		return valueList
		
	# erosion classification
	def erosionClassificationAction(self):
		self.erosionClassification()
		
	# erosion classification
	def erosionClassification(self, batch = 'No', rasterInput = None, rasterOutput = None,circularStructure = None):
		# class value list
		valueList = self.checkValueList()
		if len(valueList) > 0:
			if batch == 'No':
				outputRaster = cfg.utls.getSaveFileName(None , cfg.QtWidgetsSCP.QApplication.translate('semiautomaticclassificationplugin', 'Save output'), '', 'TIF file (*.tif);;VRT file (*.vrt)')
			else:
				outputRaster = rasterOutput
			# virtual raster
			vrtR = 'No'
			if outputRaster is not False:
				if outputRaster.lower().endswith('.vrt'):
					vrtR = 'Yes'
				elif outputRaster.lower().endswith('.tif'):
					pass
				else:
					outputRaster = outputRaster + '.tif'
				if batch == 'No':
					cfg.uiUtls.addProgressBar()
					cfg.cnvs.setRenderFlag(False)
					raster = cfg.ui.erosion_raster_name_combo.currentText()
					r = cfg.utls.selectLayerbyName(raster, 'Yes')
				else:
					r = 'No'
				if r is not None:
					if batch == 'No':
						rSource = cfg.utls.layerSource(r)
					else:
						if cfg.osSCP.path.isfile(rasterInput):
							rSource = rasterInput
						else:
							return 'No'
					if rSource is None:
						cfg.mx.msg4()
						# logger
						cfg.utls.logCondition(str(__name__) + '-' + (cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), ' None raster')
						if batch == 'No':
							cfg.uiUtls.removeProgressBar()
							cfg.cnvs.setRenderFlag(True)
						return 'No'
					cfg.uiUtls.updateBar(10)
					cfg.utls.makeDirectory(cfg.osSCP.path.dirname(outputRaster))
					input = rSource
					nd = cfg.utls.imageNoDataValue(input)
					dType = cfg.utls.getRasterDataTypeName(input)
					size =  cfg.ui.erosion_threshold_spinBox.value()
					if circularStructure is None:
						if cfg.ui.circular_structure_checkBox_3.isChecked():
							circularStructure = 'Yes'
						else:
							circularStructure = 'No'
					if circularStructure == 'No':
						structure = cfg.np.ones((3,3))
					else:
						structure = cfg.utls.createCircularStructure(1)
					# iterate
					for s in range(0, size):
						# last iteration
						if s == size-1:
							tPMD = outputRaster
							vrtRR = vrtR
						else:
							vrtRR = 'Yes'
							if vrtR == 'No':
								tPMD = cfg.utls.createTempRasterPath('tif')
							else:
								tPMD = cfg.utls.createTempRasterPath('vrt')
						# process calculation
						o = cfg.utls.multiProcessRaster(rasterPath = input, functionBand = 'No', functionRaster = cfg.utls.rasterErosion, outputRasterList = [tPMD], functionBandArgument = structure, functionVariable = valueList, progressMessage = cfg.QtWidgetsSCP.QApplication.translate('semiautomaticclassificationplugin', 'Erosion step ') + str(s+1) + '/' + str(size), virtualRaster = vrtR, compress = 'No', outputNoDataValue = nd, dataType = dType, boundarySize = 3, additionalLayer = 5)
						input = tPMD
					if cfg.osSCP.path.isfile(outputRaster):
						oR =cfg.utls.addRasterLayer(outputRaster)
					if r != 'No':
						try:
							cfg.utls.copyRenderer(r, oR)
						except:
							pass
					if batch == 'No':
						cfg.utls.finishSound()
						cfg.utls.sendSMTPMessage(None, str(__name__))
						cfg.uiUtls.removeProgressBar()
						cfg.cnvs.setRenderFlag(True)
				else:
					if batch == 'No':
						cfg.uiUtls.removeProgressBar()
						cfg.cnvs.setRenderFlag(True)
					cfg.utls.refreshClassificationLayer()
					cfg.mx.msgErr9()
					# logger
					cfg.utls.logCondition(str(__name__) + '-' + str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), "Error raster not found")
				# logger
				cfg.utls.logCondition(str(__name__) + "-" + str(cfg.inspectSCP.stack()[0][3])+ " " + cfg.utls.lineOfCode())
			