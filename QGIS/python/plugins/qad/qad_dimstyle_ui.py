# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\qad_dimstyle.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DimStyle_Dialog(object):
    def setupUi(self, DimStyle_Dialog):
        DimStyle_Dialog.setObjectName("DimStyle_Dialog")
        DimStyle_Dialog.setWindowModality(QtCore.Qt.WindowModal)
        DimStyle_Dialog.resize(539, 341)
        DimStyle_Dialog.setMinimumSize(QtCore.QSize(539, 341))
        DimStyle_Dialog.setMaximumSize(QtCore.QSize(539, 341))
        self.label = QtWidgets.QLabel(DimStyle_Dialog)
        self.label.setGeometry(QtCore.QRect(20, 10, 151, 16))
        self.label.setObjectName("label")
        self.currentDimStyle = QtWidgets.QLabel(DimStyle_Dialog)
        self.currentDimStyle.setGeometry(QtCore.QRect(180, 10, 341, 16))
        self.currentDimStyle.setObjectName("currentDimStyle")
        self.label_2 = QtWidgets.QLabel(DimStyle_Dialog)
        self.label_2.setGeometry(QtCore.QRect(10, 40, 171, 20))
        self.label_2.setObjectName("label_2")
        self.dimStyleList = QtWidgets.QListView(DimStyle_Dialog)
        self.dimStyleList.setGeometry(QtCore.QRect(10, 60, 171, 171))
        self.dimStyleList.setObjectName("dimStyleList")
        self.SetCurrent = QtWidgets.QPushButton(DimStyle_Dialog)
        self.SetCurrent.setGeometry(QtCore.QRect(410, 60, 121, 23))
        self.SetCurrent.setObjectName("SetCurrent")
        self.new_2 = QtWidgets.QPushButton(DimStyle_Dialog)
        self.new_2.setGeometry(QtCore.QRect(410, 90, 121, 23))
        self.new_2.setObjectName("new_2")
        self.Mod = QtWidgets.QPushButton(DimStyle_Dialog)
        self.Mod.setGeometry(QtCore.QRect(410, 120, 121, 23))
        self.Mod.setObjectName("Mod")
        self.TempMod = QtWidgets.QPushButton(DimStyle_Dialog)
        self.TempMod.setGeometry(QtCore.QRect(410, 150, 121, 23))
        self.TempMod.setObjectName("TempMod")
        self.Diff = QtWidgets.QPushButton(DimStyle_Dialog)
        self.Diff.setGeometry(QtCore.QRect(410, 180, 121, 23))
        self.Diff.setObjectName("Diff")
        self.groupBox = QtWidgets.QGroupBox(DimStyle_Dialog)
        self.groupBox.setGeometry(QtCore.QRect(10, 240, 521, 61))
        self.groupBox.setObjectName("groupBox")
        self.descriptionSelectedStyle = QtWidgets.QLabel(self.groupBox)
        self.descriptionSelectedStyle.setGeometry(QtCore.QRect(10, 10, 481, 41))
        self.descriptionSelectedStyle.setObjectName("descriptionSelectedStyle")
        self.label_3 = QtWidgets.QLabel(DimStyle_Dialog)
        self.label_3.setGeometry(QtCore.QRect(190, 40, 101, 16))
        self.label_3.setObjectName("label_3")
        self.selectedStyle = QtWidgets.QLabel(DimStyle_Dialog)
        self.selectedStyle.setGeometry(QtCore.QRect(300, 40, 221, 20))
        self.selectedStyle.setObjectName("selectedStyle")
        self.layoutWidget = QtWidgets.QWidget(DimStyle_Dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(370, 310, 158, 25))
        self.layoutWidget.setObjectName("layoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.closeButton = QtWidgets.QPushButton(self.layoutWidget)
        self.closeButton.setObjectName("closeButton")
        self.horizontalLayout.addWidget(self.closeButton)
        self.helpButton = QtWidgets.QPushButton(self.layoutWidget)
        self.helpButton.setObjectName("helpButton")
        self.horizontalLayout.addWidget(self.helpButton)
        self.previewDummy = QtWidgets.QPushButton(DimStyle_Dialog)
        self.previewDummy.setGeometry(QtCore.QRect(190, 60, 211, 171))
        self.previewDummy.setText("")
        self.previewDummy.setObjectName("previewDummy")

        self.retranslateUi(DimStyle_Dialog)
        self.SetCurrent.clicked.connect(DimStyle_Dialog.setCurrentStyle)
        self.new_2.clicked.connect(DimStyle_Dialog.createNewStyle)
        self.Mod.clicked.connect(DimStyle_Dialog.modStyle)
        self.dimStyleList.customContextMenuRequested['QPoint'].connect(DimStyle_Dialog.displayPopupMenu)
        self.TempMod.clicked.connect(DimStyle_Dialog.temporaryModStyle)
        self.helpButton.clicked.connect(DimStyle_Dialog.ButtonHELP_Pressed)
        self.Diff.clicked.connect(DimStyle_Dialog.showDiffBetweenStyles)
        self.closeButton.clicked.connect(DimStyle_Dialog.accept)
        QtCore.QMetaObject.connectSlotsByName(DimStyle_Dialog)

    def retranslateUi(self, DimStyle_Dialog):
        _translate = QtCore.QCoreApplication.translate
        DimStyle_Dialog.setWindowTitle(_translate("DimStyle_Dialog", "QAD - Dimension style manager"))
        self.label.setText(_translate("DimStyle_Dialog", "Current dimension style:"))
        self.currentDimStyle.setText(_translate("DimStyle_Dialog", "none"))
        self.label_2.setText(_translate("DimStyle_Dialog", "Styles"))
        self.SetCurrent.setToolTip(_translate("DimStyle_Dialog", "Sets the style selected under Styles to current. The current style is applied to dimensions you create."))
        self.SetCurrent.setText(_translate("DimStyle_Dialog", "Set current"))
        self.new_2.setToolTip(_translate("DimStyle_Dialog", "Define a new dimension style."))
        self.new_2.setText(_translate("DimStyle_Dialog", "New..."))
        self.Mod.setToolTip(_translate("DimStyle_Dialog", "Modify the selected dimension style."))
        self.Mod.setText(_translate("DimStyle_Dialog", "Modify..."))
        self.TempMod.setToolTip(_translate("DimStyle_Dialog", "Set temporary modifications for the selected style. The temporary modifications will not saved."))
        self.TempMod.setText(_translate("DimStyle_Dialog", "Override..."))
        self.Diff.setToolTip(_translate("DimStyle_Dialog", "Compare two dimension styles or list all the properties of one dimension style."))
        self.Diff.setText(_translate("DimStyle_Dialog", "Compare..."))
        self.groupBox.setTitle(_translate("DimStyle_Dialog", "Description"))
        self.descriptionSelectedStyle.setText(_translate("DimStyle_Dialog", "none"))
        self.label_3.setText(_translate("DimStyle_Dialog", "Preview of:"))
        self.selectedStyle.setText(_translate("DimStyle_Dialog", "none"))
        self.closeButton.setText(_translate("DimStyle_Dialog", "Close"))
        self.helpButton.setText(_translate("DimStyle_Dialog", "?"))
