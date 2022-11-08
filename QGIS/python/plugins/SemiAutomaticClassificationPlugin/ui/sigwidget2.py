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

# Import PyQt libraries
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget
# Import FigureCanvas
try:
	import matplotlib
except:
	pass
try:
	matplotlib.use('Qt5Agg')
except:
	pass
try:
	from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigCanvas
	# Import Figure
	from matplotlib.figure import Figure
except:
	FigCanvas = QWidget

class SigCanvas(FigCanvas):
	def __init__(self):
		try:
			# Figure
			self.figure = Figure()
			# Add subplot for plot and legend
			self.ax = self.figure.add_axes([0.1, 0.15, 0.8, 0.8])
			# Canvas initialization
			FigCanvas.__init__(self, self.figure)
		except:
			return None
		# Set empty ticks
		self.ax.set_xticks([])
		self.ax.set_yticks([])

class SigWidget2(QWidget):
	def __init__(self, parent = None):
		try:
			# Widget initialization
			QWidget.__init__(self, parent)
			# Widget canvas
			self.sigCanvas = SigCanvas()
			# Create grid layout
			self.gridLayout = QtWidgets.QGridLayout()
			# Add widget to grid
			self.gridLayout.addWidget(self.sigCanvas)
		except:
			return None
		# Set layout
		self.setLayout(self.gridLayout)