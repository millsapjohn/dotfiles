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

class CrossClassification:

	def __init__(self):
		self.clssfctnNm = None
		
	# calculate cross classification if click on button
	def calculateCrossClassification(self):
		# logger
		cfg.utls.logCondition(str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), ' calculate Cross Classification ')
		self.crossClassification(self.clssfctnNm, cfg.referenceLayer2)
	
	# classification name
	def classificationLayerName(self):
		self.clssfctnNm = cfg.ui.classification_name_combo_2.currentText()
		# logger
		cfg.utls.logCondition(str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), 'classification name: ' + str(self.clssfctnNm))
	
	# cross classification calculation
	def crossClassification(self, classification, reference, batch = 'No', shapefileField = None, rasterOutput = None,  NoDataValue = None, regressionRaster = 'No'):
		# check if numpy is updated
		try:
			cfg.np.count_nonzero([1,1,0])
		except Exception as err:
			# logger
			cfg.utls.logCondition(str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), ' ERROR exception: ' + str(err))
			rstrCheck = 'No'
			cfg.mx.msgErr26()
		if batch == 'No':
			crossRstPath = cfg.utls.getSaveFileName(None, cfg.QtWidgetsSCP.QApplication.translate('semiautomaticclassificationplugin', 'Save cross classification raster output'), '', 'TIF file (*.tif);;VRT file (*.vrt)')
		else:
			crossRstPath = rasterOutput
		# virtual raster
		vrtR = 'No'
		if crossRstPath is not False:
			if crossRstPath.lower().endswith('.vrt'):
				vrtR = 'Yes'
			elif crossRstPath.lower().endswith('.tif'):
				pass
			else:
				crossRstPath = crossRstPath + '.tif'
			if batch == 'No':
				iClass = cfg.utls.selectLayerbyName(classification, 'Yes')
				l = cfg.utls.selectLayerbyName(reference)
			else:
				try:
					# open input with GDAL
					rD = cfg.gdalSCP.Open(reference, cfg.gdalSCP.GA_ReadOnly)
					if rD is None:
						l = cfg.utls.addVectorLayer(reference, cfg.utls.fileName(reference), 'ogr')
					else:
						l = cfg.utls.addRasterLayer(reference)
					reml = l
					rD = None
					if cfg.osSCP.path.isfile(classification):
						iClass = cfg.utls.addRasterLayer(classification)
						remiClass = iClass
					else:
						return 'No'
				except:
					return 'No'
			# regression
			if batch == 'No':
				if cfg.ui.regression_raster_checkBox.isChecked() is True:
					regressionRaster = 'Yes'
			# date time for temp name
			dT = cfg.utls.getTime()
			if iClass is not None and l is not None:
				cfg.utls.makeDirectory(cfg.osSCP.path.dirname(crossRstPath))
				# if not reference shapefile
				if l.type() != 0:
					# check projections
					rCrs = cfg.utls.getCrsGDAL(cfg.utls.layerSource(l))
					rEPSG = cfg.osrSCP.SpatialReference()
					rEPSG.ImportFromWkt(rCrs)
					eCrs = cfg.utls.getCrsGDAL(cfg.utls.layerSource(iClass))
					EPSG = cfg.osrSCP.SpatialReference()
					EPSG.ImportFromWkt(eCrs)
					if EPSG.IsSame(rEPSG) != 1:
						tPMD = cfg.utls.createTempRasterPath('vrt')
						cfg.utls.createWarpedVrt(cfg.utls.layerSource(iClass), tPMD, str(rCrs))
						cfg.mx.msg9()
						remiClass2 = cfg.utls.addRasterLayer(tPMD)
						iClass = remiClass2
				else:
					# vector EPSG
					if 'Polygon?crs=' in str(cfg.utls.layerSource(l)) or 'memory?geometry=' in str(cfg.utls.layerSource(l)):
						# temp shapefile
						tSHP = cfg.utls.createTempRasterPath('gpkg')
						l = cfg.utls.saveMemoryLayerToShapefile(l, tSHP, format = 'GPKG')
						vCrs = cfg.utls.getCrsGDAL(tSHP)
						vEPSG = cfg.osrSCP.SpatialReference()
						vEPSG.ImportFromWkt(vCrs)
					else:
						ql = cfg.utls.layerSource(l)
						vCrs = cfg.utls.getCrsGDAL(ql)
						vEPSG = cfg.osrSCP.SpatialReference()
						vEPSG.ImportFromWkt(vCrs)
					# in case of reprojection
					qll = cfg.utls.layerSource(l)
					reprjShapefile = cfg.tmpDir + '/' + dT + cfg.utls.fileName(qll)
					qlll = cfg.utls.layerSource(iClass)
					rCrs = cfg.utls.getCrsGDAL(qlll)
					rEPSG = cfg.osrSCP.SpatialReference()
					rEPSG.ImportFromWkt(rCrs)
					if vEPSG.IsSame(rEPSG) != 1:
						if cfg.osSCP.path.isfile(reprjShapefile):
							pass
						else:
							try:
								qllll = cfg.utls.layerSource(l)
								cfg.utls.repojectShapefile(qllll, vEPSG, reprjShapefile, rEPSG)
							except Exception as err:
								# remove temp layers
								try:
									cfg.utls.removeLayerByLayer(reml)
								except:
									pass
								try:
									cfg.utls.removeLayerByLayer(remiClass)
								except:
									pass
								try:
									cfg.utls.removeLayerByLayer(remiClass2)
								except:
									pass
								# logger
								cfg.utls.logCondition(str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), ' ERROR exception: ' + str(err))
								return 'No'
						l = cfg.utls.addVectorLayer(reprjShapefile, cfg.utls.fileName(reprjShapefile) , 'ogr')
				if batch == 'No':
					cfg.uiUtls.addProgressBar()
					# disable map canvas render for speed
					cfg.cnvs.setRenderFlag(False)
					cfg.QtWidgetsSCP.qApp.processEvents()
				# temp raster layer
				tRC = cfg.utls.createTempRasterPath('tif')
				# cross classification
				eMN = dT + cfg.crossClassNm
				cfg.reportPth = str(cfg.tmpDir + '/' + eMN)
				tblOut = cfg.osSCP.path.dirname(crossRstPath) + '/' + cfg.utls.fileNameNoExt(crossRstPath) + '.csv'
				cfg.uiUtls.updateBar(10)
				# if reference shapefile
				if l.type() == cfg.qgisCoreSCP.QgsMapLayer.VectorLayer:
					if batch == 'No':
						fd = cfg.ui.class_field_comboBox_2.currentText()
					else:
						fd = shapefileField
					if batch == 'No':
						# convert reference layer to raster
						qlllll = cfg.utls.layerSource(l)
						qllllll = cfg.utls.layerSource(iClass)
						vect = cfg.utls.vectorToRaster(fd, str(qlllll), classification, str(tRC), str(qllllll), extent = 'Yes')
					else:
						qlllllll = cfg.utls.layerSource(l)
						vect = cfg.utls.vectorToRaster(fd, str(qlllllll), classification, str(tRC), classification, extent = 'Yes')
					if vect == 'No':
						if batch == 'No':
							# enable map canvas render
							cfg.cnvs.setRenderFlag(True)
							cfg.uiUtls.removeProgressBar()
						return 'No'	
					referenceRaster = tRC
				# if reference raster
				elif l.type() == cfg.qgisCoreSCP.QgsMapLayer.RasterLayer:
					if batch == 'No':
						referenceRaster = cfg.utls.layerSource(l)
					else:
						referenceRaster = reference
				# No data value
				if NoDataValue is not None:
					nD = NoDataValue
				elif cfg.ui.nodata_checkBox_6.isChecked() is True:
					nD = cfg.ui.nodata_spinBox_7.value()
				else:
					nD = None
				# create virtual raster
				qlllllllI = cfg.utls.layerSource(iClass)
				bList = [referenceRaster, qlllllllI]
				bListNum = [1, 1]
				vrtCheck = cfg.utls.createTempVirtualRaster(bList, bListNum, 'Yes', 'Yes', 0, 'No', 'Yes')
				bandsUniqueVal = []
				k = []
				for b in bList:
					cfg.parallelArrayDict = {}
					o = cfg.utls.multiProcessRaster(rasterPath = b, functionBand = 'No', functionRaster = cfg.utls.rasterUniqueValuesWithSum, nodataValue = nD, progressMessage = cfg.QtWidgetsSCP.QApplication.translate('semiautomaticclassificationplugin', 'Unique values'))
					# calculate unique values
					values = cfg.np.array([])
					for x in sorted(cfg.parallelArrayDict):
						try:
							for ar in cfg.parallelArrayDict[x]:
								values = cfg.np.append(values, ar[0][0, ::])
						except:
							if batch == 'No':
								cfg.utls.finishSound()
								cfg.utls.sendSMTPMessage(None, str(__name__))
								# enable map canvas render
								cfg.cnvs.setRenderFlag(True)
								cfg.uiUtls.removeProgressBar()			
							# logger
							cfg.utls.logCondition(str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), ' ERROR values')
							cfg.mx.msgErr9()		
							return 'No'
					rasterBandUniqueVal = cfg.np.unique(values).tolist()
					refRasterBandUniqueVal = sorted(rasterBandUniqueVal)
					try:
						refRasterBandUniqueVal.remove(nD)
					except:
						pass
					bandsUniqueVal.append(refRasterBandUniqueVal)
					if 0 in refRasterBandUniqueVal:
						k.append(1)
					else:
						k.append(0)
				try:
					cmb = list(cfg.itertoolsSCP.product(*bandsUniqueVal))
					testCmb = cmb[0]
				except Exception as err:
					if batch == 'No':
						cfg.uiUtls.removeProgressBar()
					cfg.mx.msgErr63()
					# logger
					cfg.utls.logCondition(str(__name__) + '-' + str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), ' ERROR exception: ' + str(err))
					return 'No'
				# expression builder
				check = 'No'
				t = 0
				while t < 100:
					t = t + 1
					rndVarList = []
					calcDataType = cfg.np.uint32
					# first try fixed list
					if t == 1:
						coT = 333
						for cmbI in range(0, len(cmb[0])):
							rndVarList.append(coT)
							coT = coT + 1
					# random list
					else:
						for cmbI in range(0, len(cmb[0])):
							rndVarList.append(int(999 * cfg.np.random.random()))
					newValueList = []
					reclassDict = {}
					for i in cmb:
						newVl = (i[0] + k[0]) * (rndVarList[0]) + (i[1] + k[1]) * (rndVarList[1])
						reclassDict[newVl] = i
						newValueList.append(newVl)
						if i[0] < 0 or i[1] < 0 :
							calcDataType = cfg.np.int32
					uniqueValList = cfg.np.unique(newValueList)
					if int(uniqueValList.shape[0]) == len(newValueList):
						n = 1
						col = []
						row = []
						reclassList = []
						cmbntns = {}	
						for newVl in sorted(reclassDict.keys()):
							i = reclassDict[newVl]
							reclassList.append(newVl)
							cmbntns[n] = [i[1], i[0]]
							col.append(i[1])
							row.append(i[0])
							n = n + 1
						check = 'Yes'
						break
				if check == 'No':
					if batch == 'No':
						# enable map canvas render
						cfg.cnvs.setRenderFlag(True)
						cfg.uiUtls.removeProgressBar()
					return 'No'
				e = '(rasterSCPArrayfunctionBand[::, ::, 0] + ' + str(k[0]) +' ) * ' + str(rndVarList[0]) + ' + (rasterSCPArrayfunctionBand[::, ::, 1] + ' + str(k[1]) +' ) * ' + str(rndVarList[1])
				# check projections
				left, right, top, bottom, cRPX, cRPY, rP, un = cfg.utls.imageGeoTransform(vrtCheck)					
				# calculation
				cfg.parallelArrayDict = {}
				o = cfg.utls.multiProcessRaster(rasterPath = vrtCheck, functionBand = 'No', functionRaster = cfg.utls.crossRasters, outputRasterList = [crossRstPath], nodataValue = nD,  functionBandArgument = reclassList, functionVariable = e, progressMessage = cfg.QtWidgetsSCP.QApplication.translate('semiautomaticclassificationplugin', 'Cross classification'), outputNoDataValue = cfg.NoDataValUInt32,  virtualRaster = vrtR, compress = cfg.rasterCompression, dataType = 'UInt32', calcDataType = calcDataType)
				cfg.uiUtls.updateBar(60)
				if o == 'No':
					if batch == 'No':
						# enable map canvas render
						cfg.cnvs.setRenderFlag(True)
						cfg.uiUtls.removeProgressBar()
					cfg.mx.msgErr45()
					# remove temp layers
					try:
						cfg.utls.removeLayerByLayer(reml)
					except:
						pass
					try:
						cfg.utls.removeLayerByLayer(remiClass)
					except:
						pass
					try:
						cfg.utls.removeLayerByLayer(remiClass2)
					except:
						pass
					# logger
					cfg.utls.logCondition(str(__name__) + '-' + str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), 'Error')
					return 'No'
				# logger
				cfg.utls.logCondition(str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), 'cross raster output: ' + str(crossRstPath))
				# calculate unique values
				values = cfg.np.array([])
				sumVal = cfg.np.array([])
				for x in sorted(cfg.parallelArrayDict):
					try:
						for ar in cfg.parallelArrayDict[x]:
							values = cfg.np.append(values, ar[1][0, ::])
							sumVal = cfg.np.append(sumVal, ar[1][1, ::])
					except:
						if batch == 'No':
							cfg.utls.finishSound()
							cfg.utls.sendSMTPMessage(None, str(__name__))
							# enable map canvas render
							cfg.cnvs.setRenderFlag(True)
							cfg.uiUtls.removeProgressBar()			
						# logger
						cfg.utls.logCondition(str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), ' ERROR values')
						cfg.mx.msgErr9()		
						return 'No'
				reclRasterBandUniqueVal = {}
				values = values.astype(int)
				for v in range(0, len(values)):
					try:
						reclRasterBandUniqueVal[values[v]] = reclRasterBandUniqueVal[values[v]] + sumVal[v]
					except:
						reclRasterBandUniqueVal[values[v]] = sumVal[v]
				rasterBandUniqueVal = {}
				for v in range(0, len(values)):
					try:
						cmbX = cmbntns[values[v]]
						rasterBandUniqueVal[(cmbX[0], cmbX[1])] = [reclRasterBandUniqueVal[values[v]], values[v]]
					except:
						pass
				cfg.uiUtls.updateBar(80)
				col2 = list(set(col))
				row2 = list(set(row))
				cols = sorted(cfg.np.unique(col2).tolist())
				rows = sorted(cfg.np.unique(row2).tolist())
				crossClass = cfg.np.zeros((len(rows), len(cols)))
				cList = 'V_' + cfg.QtWidgetsSCP.QApplication.translate('semiautomaticclassificationplugin', 'Reference') + '\t'
				try:
					l = open(tblOut, 'w')
				except Exception as err:
					# remove temp layers
					try:
						cfg.utls.removeLayerByLayer(reml)
					except:
						pass
					try:
						cfg.utls.removeLayerByLayer(remiClass)
					except:
						pass
					try:
						cfg.utls.removeLayerByLayer(remiClass2)
					except:
						pass
					# logger
					cfg.utls.logCondition(str(__name__) + '-' + str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), ' ERROR exception: ' + str(err))
					return 'No'
				t = cfg.QtWidgetsSCP.QApplication.translate('semiautomaticclassificationplugin', 'CrossClassCode') + '	' + cfg.QtWidgetsSCP.QApplication.translate('semiautomaticclassificationplugin', 'Classification') + '	' + cfg.QtWidgetsSCP.QApplication.translate('semiautomaticclassificationplugin', 'Reference') + '	' + cfg.QtWidgetsSCP.QApplication.translate('semiautomaticclassificationplugin', 'PixelSum') + '	' + cfg.QtWidgetsSCP.QApplication.translate('semiautomaticclassificationplugin', 'Area [' + un + '^2]') + str('\n')
				l.write(t)
				rSumX = 0
				rSumY = 0
				rSumTot = 0
				for c in cols:
					cList = cList + str(int(c)) + '\t'
					for r in rows:
						try:
							v = (c, r)
							area = str(round(rasterBandUniqueVal[v][0] * cRPX * cRPY, 5))
							t = str(rasterBandUniqueVal[v][1]) + '\t' + str(int(c)) + '\t' + str(int(r)) + '\t' + str(int(rasterBandUniqueVal[v][0])) + '\t' + area + str('\n')
							l.write(t)
							crossClass[rows.index(r), cols.index(c)] = rasterBandUniqueVal[v][0] * cRPX * cRPY
							rSumX = rSumX + c * rasterBandUniqueVal[v][0]
							rSumY = rSumY + r * rasterBandUniqueVal[v][0]
							rSumTot = rSumTot + rasterBandUniqueVal[v][0]
						except:
							crossClass[rows.index(r), cols.index(c)] = 0
				# calculate regression
				if regressionRaster == 'Yes':
					rXMean = rSumX / rSumTot
					rYMean = rSumY / rSumTot
					# linear regression y = b0 + b1 x + E
					Sxy = 0
					Sxx = 0
					Syy = 0
					for c in cols:
						for r in rows:
							try:
								v = (c, r)
								Sxx = Sxx + rasterBandUniqueVal[v][0] * (c - rXMean)**2
								Syy = Syy + rasterBandUniqueVal[v][0] * (r - rYMean)**2
								Sxy = Sxy + (c - rXMean) * (r - rYMean) * rasterBandUniqueVal[v][0]
							except:
								pass
					try:
						rCoeff = Sxy / (Sxx * Syy)**0.5
						rCoeff2 = rCoeff**2
						slope = Sxy / Sxx
						intercept = rYMean - slope * rXMean
						VAR_Y = (Syy - slope * Sxy) / (rSumTot-2)
						VAR_slope = VAR_Y / Sxx
						VAR_intercept = VAR_Y * ( 1/rSumTot + rXMean**2 / Sxx)
						conf_slope = 2 * (VAR_slope)**0.5
						conf_intercept = 2 * (VAR_intercept)**0.5
					except:
						rCoeff = ''
						rCoeff2 = ''
						slope = ''
						intercept = ''
						VAR_Y = ''
						VAR_slope = ''
						conf_slope = ''
						VAR_intercept = ''
						conf_intercept = ''
				# save combination to table
				l.write(str('\n'))
				tStr = '\t' + '> ' + cfg.QtWidgetsSCP.QApplication.translate('semiautomaticclassificationplugin', 'CROSS MATRIX [') + str(un) + '^2]' + '\n'
				l.write(tStr)
				tStr = '\t' + '> ' + cfg.QtWidgetsSCP.QApplication.translate('semiautomaticclassificationplugin', 'Classification') + '\n'
				l.write(tStr)
				tStr = cList + cfg.QtWidgetsSCP.QApplication.translate('semiautomaticclassificationplugin', 'Total') + '\n'
				l.write(tStr)
				# temp matrix
				tmpMtrx= cfg.tmpDir + '/' + cfg.tempMtrxNm + dT + '.txt'
				cfg.np.savetxt(tmpMtrx, crossClass, delimiter='\t', fmt='%i')
				tM = open(tmpMtrx, 'r')
				# write matrix
				ix = 0
				for j in tM:
					tMR = str(int(rows[ix])) + '\t' + j.rstrip('\n') + '\t' + str(int(crossClass[ix, :].sum())) + str('\n')
					l.write(tMR)
					ix = ix + 1
				# last line
				lL = cfg.QtWidgetsSCP.QApplication.translate('semiautomaticclassificationplugin', 'Total')
				for c in range(0, len(cols)):
					lL = lL + '\t' + str(int(crossClass[:, c].sum()))
				totMat = int(crossClass.sum())
				lL = lL + '\t' + str(totMat) + str('\n')
				l.write(lL)
				# write linear regression
				if regressionRaster == 'Yes':
					l.write(str('\n'))
					l.write('Linear regression Y = B0 + B1*X' + '\n')
					l.write('Coeff. det. R^2' + '\t' + str(rCoeff2) + '\n')
					l.write('Coeff. correlation r' + '\t' + str(rCoeff) + '\n')
					l.write('B1' + '\t' + str(slope) + ' ± ' + str(conf_slope) + ' \n')
					l.write('B0' + '\t' + str(intercept) + ' ± ' + str(conf_intercept) + '\n')
					l.write('Variance Y' + '\t' + str(VAR_Y) + '\n')
					l.write('Variance B1' + '\t' + str(VAR_slope) + '\n')
					l.write('Variance B0' + '\t' + str(VAR_intercept) + '\n')
				l.close()
				# add raster to layers
				rastUniqueVal = cfg.np.unique(values).tolist()
				rstr = cfg.utls.addRasterLayer(crossRstPath)
				cfg.utls.rasterSymbolGeneric(rstr, 'NoData', rasterUniqueValueList = rastUniqueVal)	
				try:
					f = open(tblOut)
					if cfg.osSCP.path.isfile(tblOut):
						eM = f.read()
						cfg.ui.cross_matrix_textBrowser.setText(eM)
					# logger
					cfg.utls.logCondition(str(__name__) + '-' + str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), ' cross matrix calculated')
				except Exception as err:
					# logger
					cfg.utls.logCondition(str(__name__) + '-' + str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), ' ERROR exception: ' + str(err))
				if regressionRaster == 'Yes':
					# logger
					cfg.utls.logCondition(str(__name__) + '-' + str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), ' regression raster')
					# output rasters
					outRasterB0 = cfg.osSCP.path.dirname(crossRstPath) + '/' + cfg.utls.fileNameNoExt(crossRstPath) + '_b0.tif'
					oM = []
					oM.append(outRasterB0)
					try:
						rDD = cfg.gdalSCP.Open(vrtCheck, cfg.gdalSCP.GA_ReadOnly)
						oMR = cfg.utls.createRasterFromReference(rDD, 1, oM, cfg.NoDataVal, 'GTiff', 'Float32', 0, None, cfg.rasterCompression, 'LZW', constantValue = intercept)
						# close GDAL rasters
						for b in range(0, len(oMR)):
							oMR[b] = None
						# add raster to layers
						rstr = cfg.utls.addRasterLayer(outRasterB0)
					except Exception as err:
						# logger
						cfg.utls.logCondition(str(__name__) + '-' + str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), ' ERROR exception: ' + str(err))
					outRasterB1 = cfg.osSCP.path.dirname(crossRstPath) + '/' + cfg.utls.fileNameNoExt(crossRstPath) + '_b1.tif'
					oM = []
					oM.append(outRasterB1)
					try:
						oMR = cfg.utls.createRasterFromReference(rDD, 1, oM, cfg.NoDataVal, 'GTiff', 'Float32', 0, None, cfg.rasterCompression, 'LZW', constantValue = slope)
						# close GDAL rasters
						for b in range(0, len(oMR)):
							oMR[b] = None
						# add raster to layers
						rstr = cfg.utls.addRasterLayer(outRasterB1)
						rDD = None
					except Exception as err:
						# logger
						cfg.utls.logCondition(str(__name__) + '-' + str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), ' ERROR exception: ' + str(err))
				cfg.uiUtls.updateBar(100)
				# remove temp layers
				try:
					cfg.utls.removeLayerByLayer(reml)
				except:
					pass
				try:
					cfg.utls.removeLayerByLayer(remiClass)
				except:
					pass
				try:
					cfg.utls.removeLayerByLayer(remiClass2)
				except:
					pass
				if batch == 'No':
					# enable map canvas render
					cfg.cnvs.setRenderFlag(True)
					cfg.utls.finishSound()
					cfg.utls.sendSMTPMessage(None, str(__name__))
					cfg.ui.toolBox_cross_classification.setCurrentIndex(1)
					cfg.uiUtls.removeProgressBar()
				# logger
				cfg.utls.logCondition(str(__name__) + '-' + str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), 'finished')
			else:
				self.refreshReferenceLayer()
				cfg.utls.refreshClassificationLayer()
				
	# reference layer name
	def referenceLayerName(self):
		cfg.referenceLayer2 = cfg.ui.reference_name_combo_2.currentText()
		cfg.ui.class_field_comboBox_2.clear()
		l = cfg.utls.selectLayerbyName(cfg.referenceLayer2)
		try:
			if l.type() == cfg.qgisCoreSCP.QgsMapLayer.VectorLayer:
				f = l.dataProvider().fields()
				for i in f:
					if str(i.typeName()).lower() != 'string':
						cfg.dlg.class_field_combo_2(str(i.name()))
		except:
			pass
		# logger
		cfg.utls.logCondition(str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), 'reference layer name: ' + str(cfg.referenceLayer2))
	
	# refresh reference layer name
	def refreshReferenceLayer(self):
		ls = cfg.qgisCoreSCP.QgsProject.instance().mapLayers().values()
		cfg.ui.reference_name_combo_2.clear()
		# reference layer name
		cfg.referenceLayer2 = None
		for l in sorted(ls, key=lambda c: c.name()):
			if (l.type() == cfg.qgisCoreSCP.QgsMapLayer.VectorLayer):
				if (l.wkbType() == cfg.qgisCoreSCP.QgsWkbTypes.Polygon) or (l.wkbType() == cfg.qgisCoreSCP.QgsWkbTypes.MultiPolygon):
					cfg.dlg.reference_layer_combo_2(l.name())
			elif (l.type() == cfg.qgisCoreSCP.QgsMapLayer.RasterLayer):
				if l.bandCount() == 1:
					cfg.dlg.reference_layer_combo_2(l.name())
		# logger
		cfg.utls.logCondition(str(cfg.inspectSCP.stack()[0][3])+ ' ' + cfg.utls.lineOfCode(), 'reference layers refreshed')
