# -*- coding: utf-8 -*-

# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 sliptonic <shopinthewoods@gmail.com>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

import FreeCAD
import FreeCADGui
import Path
import PathScripts.PathContour as PathContour
import PathScripts.PathLog as PathLog

from PathScripts import PathUtils
from PySide import QtCore, QtGui

def translate(context, text, disambig=None):
    return QtCore.QCoreApplication.translate(context, text, disambig)

class _ViewProviderContour:

    def __init__(self, vobj):
        PathLog.track()
        vobj.Proxy = self

    def attach(self, vobj):
        PathLog.track()
        self.Object = vobj.Object
        return

    def deleteObjectsOnReject(self):
        PathLog.track()
        return hasattr(self, 'deleteOnReject') and self.deleteOnReject

    def setEdit(self, vobj, mode=0):
        PathLog.track()
        FreeCADGui.Control.closeDialog()
        taskd = TaskPanel(vobj.Object, self.deleteObjectsOnReject())
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        taskd.setupUi()
        self.deleteOnReject = False
        return True

    def getIcon(self):
        return ":/icons/Path-Contour.svg"

    def __getstate__(self):
        PathLog.track()
        return None

    def __setstate__(self, state):
        PathLog.track()
        return None


class _CommandSetStartPoint:
    def GetResources(self):
        return {'Pixmap': 'Path-StartPoint',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Path_Contour", "Pick Start Point"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Path_Contour", "Pick Start Point")}

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def setpoint(self, point, o):
        obj = FreeCADGui.Selection.getSelection()[0]
        obj.StartPoint.x = point.x
        obj.StartPoint.y = point.y
        obj.StartPoint.z = obj.ClearanceHeight.Value

    def Activated(self):
        FreeCADGui.Snapper.getPoint(callback=self.setpoint)

def Create(name):
    FreeCAD.ActiveDocument.openTransaction(translate("Path", "Create a Contour"))
    obj   = PathContour.Create(name)
    vobj  = _ViewProviderContour(obj.ViewObject)

    obj.ViewObject.Proxy.deleteOnReject = True

    FreeCAD.ActiveDocument.commitTransaction()
    obj.ViewObject.startEditing()

class CommandPathContour:
    def GetResources(self):
        return {'Pixmap': 'Path-Contour',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("PathContour", "Contour"),
                'Accel': "P, C",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("PathContour", "Creates a Contour Path for the Base Object ")}

    def IsActive(self):
        if FreeCAD.ActiveDocument is not None:
            for o in FreeCAD.ActiveDocument.Objects:
                if o.Name[:3] == "Job":
                        return True
        return False

    def Activated(self):
        return Create("Contour")

class TaskPanel:
    def __init__(self, obj, deleteOnReject):
        FreeCAD.ActiveDocument.openTransaction(translate("Path_Contour", "Contour Operation"))
        self.form = FreeCADGui.PySideUic.loadUi(":/panels/ContourEdit.ui")
        self.deleteOnReject = deleteOnReject
        self.isDirty = True

    def accept(self):
        FreeCADGui.Control.closeDialog()
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCADGui.Selection.removeObserver(self.s)
        if self.isDirty:
            FreeCAD.ActiveDocument.recompute()

    def reject(self):
        FreeCADGui.Control.closeDialog()
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.abortTransaction()
        FreeCADGui.Selection.removeObserver(self.s)
        if self.deleteOnReject:
            FreeCAD.ActiveDocument.openTransaction(translate("Path_Contour", "Uncreate Contour Operation"))
            FreeCAD.ActiveDocument.removeObject(self.obj.Name)
            FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()

    def clicked(self, button):
        if button == QtGui.QDialogButtonBox.Apply:
            self.getFields()
            FreeCAD.ActiveDocument.recompute()
            self.isDirty = False

    def getFields(self):
        PathLog.track()
        if self.obj:
            if hasattr(self.obj, "StartDepth"):
                self.obj.StartDepth = FreeCAD.Units.Quantity(self.form.startDepth.text()).Value
            if hasattr(self.obj, "FinalDepth"):
                self.obj.FinalDepth = FreeCAD.Units.Quantity(self.form.finalDepth.text()).Value
            if hasattr(self.obj, "SafeHeight"):
                self.obj.SafeHeight = FreeCAD.Units.Quantity(self.form.safeHeight.text()).Value
            if hasattr(self.obj, "ClearanceHeight"):
                self.obj.ClearanceHeight = FreeCAD.Units.Quantity(self.form.clearanceHeight.text()).Value
            if hasattr(self.obj, "StepDown"):
                self.obj.StepDown = FreeCAD.Units.Quantity(self.form.stepDown.text()).Value
            if hasattr(self.obj, "OffsetExtra"):
                self.obj.OffsetExtra = FreeCAD.Units.Quantity(self.form.extraOffset.text()).Value
            if hasattr(self.obj, "UseComp"):
                self.obj.UseComp = self.form.useCompensation.isChecked()
            # if hasattr(self.obj, "UseStartPoint"):
            #     self.obj.UseStartPoint = self.form.useStartPoint.isChecked()
            if hasattr(self.obj, "Direction"):
                self.obj.Direction = str(self.form.direction.currentText())
            if hasattr(self.obj, "ToolController"):
                tc = PathUtils.findToolController(self.obj, self.form.uiToolController.currentText())
                self.obj.ToolController = tc
        self.isDirty = True

    def setFields(self):
        PathLog.track()
        self.form.startDepth.setText(FreeCAD.Units.Quantity(self.obj.StartDepth.Value, FreeCAD.Units.Length).UserString)
        self.form.finalDepth.setText(FreeCAD.Units.Quantity(self.obj.FinalDepth.Value, FreeCAD.Units.Length).UserString)
        self.form.stepDown.setText(FreeCAD.Units.Quantity(self.obj.StepDown.Value, FreeCAD.Units.Length).UserString)
        self.form.safeHeight.setText(FreeCAD.Units.Quantity(self.obj.SafeHeight.Value, FreeCAD.Units.Length).UserString)
        self.form.clearanceHeight.setText(FreeCAD.Units.Quantity(self.obj.ClearanceHeight.Value,  FreeCAD.Units.Length).UserString)
        self.form.extraOffset.setText(FreeCAD.Units.Quantity(self.obj.OffsetExtra.Value, FreeCAD.Units.Length).UserString)
        self.form.useCompensation.setChecked(self.obj.UseComp)
        # self.form.useStartPoint.setChecked(self.obj.UseStartPoint)

        index = self.form.direction.findText(
                self.obj.Direction, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.form.direction.blockSignals(True)
            self.form.direction.setCurrentIndex(index)
            self.form.direction.blockSignals(False)

        controllers = PathUtils.getToolControllers(self.obj)
        labels = [c.Label for c in controllers]
        self.form.uiToolController.blockSignals(True)
        self.form.uiToolController.addItems(labels)
        self.form.uiToolController.blockSignals(False)

        if self.obj.ToolController is None:
            self.obj.ToolController = PathUtils.findToolController(self.obj)

        if self.obj.ToolController is not None:
            index = self.form.uiToolController.findText(
                self.obj.ToolController.Label, QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.form.uiToolController.blockSignals(True)
                self.form.uiToolController.setCurrentIndex(index)
                self.form.uiToolController.blockSignals(False)
        else:
            self.obj.ToolController = PathUtils.findToolController(self.obj)

    def open(self):
        self.s = SelObserver()
        # install the function mode resident
        FreeCADGui.Selection.addObserver(self.s)

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Cancel)

    def setupUi(self):
        PathLog.track()
        # Connect Signals and Slots
        # Depths
        self.form.startDepth.editingFinished.connect(self.getFields)
        self.form.finalDepth.editingFinished.connect(self.getFields)
        self.form.stepDown.editingFinished.connect(self.getFields)

        # Heights
        self.form.safeHeight.editingFinished.connect(self.getFields)
        self.form.clearanceHeight.editingFinished.connect(self.getFields)

        # operation
        self.form.direction.currentIndexChanged.connect(self.getFields)
        self.form.uiToolController.currentIndexChanged.connect(self.getFields)
        self.form.useCompensation.clicked.connect(self.getFields)
        self.form.useStartPoint.clicked.connect(self.getFields)
        self.form.extraOffset.editingFinished.connect(self.getFields)

        self.setFields()


class SelObserver:
    def __init__(self):
        import PathScripts.PathSelection as PST
        PST.contourselect()

    def __del__(self):
        import PathScripts.PathSelection as PST
        PST.clear()

    def addSelection(self, doc, obj, sub, pnt):
        FreeCADGui.doCommand('Gui.Selection.addSelection(FreeCAD.ActiveDocument.' + obj + ')')
        FreeCADGui.updateGui()


if FreeCAD.GuiUp:
    # register the FreeCAD command
    FreeCADGui.addCommand('Path_Contour', CommandPathContour())
    FreeCADGui.addCommand('Set_StartPoint', _CommandSetStartPoint())

FreeCAD.Console.PrintLog("Loading PathContourGui... done\n")