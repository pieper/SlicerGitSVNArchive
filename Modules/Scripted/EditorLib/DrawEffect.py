import os
from __main__ import vtk
from __main__ import ctk
from __main__ import qt
from __main__ import slicer
from EditOptions import EditOptions
from EditorLib import EditorLib
import LabelEffect


#########################################################
#
# 
comment = """

  DrawEffect is a subclass of LabelEffect
  that implements the interactive paintbrush tool
  in the slicer editor

# TODO : 
"""
#
#########################################################

#
# DrawEffectOptions - see LabelEffect, EditOptions and Effect for superclasses
#

class DrawEffectOptions(LabelEffect.LabelEffectOptions):
  """ DrawEffect-specfic gui
  """

  def __init__(self, parent=0):
    super(DrawEffectOptions,self).__init__(parent)

  def __del__(self):
    super(DrawEffectOptions,self).__del__()

  def create(self):
    super(DrawEffectOptions,self).create()

    self.apply = qt.QPushButton("Apply", self.frame)
    self.apply.setToolTip("Apply current outline.\nUse the 'a' or 'Enter' hotkey to apply in slice window")
    self.frame.layout().addWidget(self.apply)
    self.widgets.append(self.apply)

    EditorLib.HelpButton(self.frame, "Use this tool to draw an outline.\n\nLeft Click: add point.\nLeft Drag: add multiple points.\nx: delete last point.\na: apply outline.")

    self.apply.connect('clicked()', self.onApply)

    # Add vertical spacer
    self.frame.layout().addStretch(1)

  def onApply(self):
    for tool in self.tools:
      tool.apply()

  def destroy(self):
    super(DrawEffectOptions,self).destroy()

  # note: this method needs to be implemented exactly as-is
  # in each leaf subclass so that "self" in the observer
  # is of the correct type 
  def updateParameterNode(self, caller, event):
    node = self.editUtil.getParameterNode()
    if node != self.parameterNode:
      if self.parameterNode:
        node.RemoveObserver(self.parameterNodeTag)
      self.parameterNode = node
      self.parameterNodeTag = node.AddObserver("ModifiedEvent", self.updateGUIFromMRML)

  def setMRMLDefaults(self):
    super(DrawEffectOptions,self).setMRMLDefaults()

  def updateGUIFromMRML(self,caller,event):
    self.updatingGUI = True
    super(DrawEffectOptions,self).updateGUIFromMRML(caller,event)
    self.updatingGUI = False

  def updateMRMLFromGUI(self):
    if self.updatingGUI:
      return
    disableState = self.parameterNode.GetDisableModifiedEvent()
    self.parameterNode.SetDisableModifiedEvent(1)
    super(DrawEffectOptions,self).updateMRMLFromGUI()
    self.parameterNode.SetDisableModifiedEvent(disableState)
    if not disableState:
      self.parameterNode.InvokePendingModifiedEvent()

#
# DrawEffectTool
#
 
class DrawEffectTool(LabelEffect.LabelEffectTool):
  """
  One instance of this will be created per-view when the effect
  is selected.  It is responsible for implementing feedback and
  label map changes in response to user input.
  This class observes the editor parameter node to configure itself
  and queries the current view for background and label volume
  nodes to operate on.
  """

  def __init__(self, sliceWidget):
    super(DrawEffectTool,self).__init__(sliceWidget)
    
    # create a logic instance to do the non-gui work
    self.logic = DrawEffectLogic(self.sliceWidget.sliceLogic())
    self.logic.undoRedo = self.undoRedo

    # interaction state variables
    self.activeSlice = None
    self.lastInsertSLiceNodeMTime = None
    self.actionState = None

    # initialization
    self.xyPoints = vtk.vtkPoints()
    self.rasPoints = vtk.vtkPoints()
    self.polyData = self.createPolyData()

    self.mapper = vtk.vtkPolyDataMapper2D()
    self.actor = vtk.vtkActor2D()
    self.mapper.SetInput(self.polyData)
    self.actor.SetMapper(self.mapper)
    property_ = self.actor.GetProperty()
    property_.SetColor(1,1,0)
    property_.SetLineWidth(1)
    self.renderer.AddActor2D( self.actor )
    self.actors.append( self.actor )

  def cleanup(self):
    """
    call superclass to clean up actor
    """
    super(DrawEffectTool,self).cleanup()

  def setLineMode(self,mode="solid"):
    property_ = self.actor.GetProperty()
    if mode == "solid":
      property_.SetLineStipplePattern(65535)
    elif mode == "dashed":
      property_.SetLineStipplePattern(0xff00)

  def processEvent(self, caller=None, event=None):
    """
    handle events from the render window interactor
    """

    # TODO: might need preProcessEvent method like DrawEffect.tcl
    # TODO: might need grabID

    # events from the interactory
    if event == "LeftButtonPressEvent":
      self.actionState = "drawing"
      xy = self.interactor.GetEventPosition()
      self.addPoint(self.logic.xyToRAS(xy))
      self.abortEvent(event)
    elif event == "LeftButtonPressEvent":
      self.actionState = ""
    elif event == "RightButtonPressEvent":
      sliceNode = self.sliceWidget.sliceLogic().GetSliceNode()
      self.lastInsertSLiceNodeMTime = sliceNode.GetMTime()
    elif event == "RightButtonReleaseEvent":
      sliceNode = self.sliceWidget.sliceLogic().GetSliceNode()
      if self.lastInsertSLiceNodeMTime == sliceNode.GetMTime():
        self.apply()
        self.actionState = None
    elif event == "MouseMoveEvent":
      if self.actionState == "drawing":
        xy = self.interactor.GetEventPosition()
        self.addPoint(self.logic.xyToRAS(xy))
        self.abortEvent(event)
    elif event == "LeaveEvent":
      self.actor.VisibilityOff()
    elif event == "KeyPressEvent":
      key = self.interactor.GetKeySym()
      if key == 'a' or key == 'Return':
        self.apply()
        self.abortEvent(event)
      if key == 'x':
        self.deleteLastPoint()
        self.abortEvent(event)
    else:
      print(caller,event,self.sliceWidget.sliceLogic().GetSliceNode().GetName())

    # events from the slice node
    if caller and caller.IsA('vtkMRMLSliceNode'):
      # 
      # make sure all points are on the current slice plane
      # - if the SliceToRAS has been modified, then we're on a different plane
      #
      sliceLogic = self.sliceWidget.sliceLogic()
      lineMode = "solid"
      currentSlice = sliceLogic.GetSliceOffset()
      if self.activeSlice:
        offset = abs(currentSlice - self.activeSlice)
        if offset > 0.01:
          lineMode = "dashed"
      self.setLineMode(lineMode)

    self.positionActors()

  def positionActors(self):
    """
    update draw feedback to follow slice node
    """
    sliceLogic = self.sliceWidget.sliceLogic()
    sliceNode = sliceLogic.GetSliceNode()
    rasToXY = vtk.vtkTransform()
    rasToXY.SetMatrix( sliceNode.GetXYToRAS() )
    rasToXY.Inverse()
    self.xyPoints.Reset()
    rasToXY.TransformPoints( self.rasPoints, self.xyPoints )
    self.polyData.Modified()
    self.sliceView.scheduleRender()

  def apply(self):

    lines = self.polyData.GetLines()
    if lines.GetNumberOfCells() == 0: return

    # close the polyline back to the first point
    idArray = lines.GetData()
    p = idArray.GetTuple1(1)
    idArray.InsertNextTuple1(p)
    idArray.SetTuple1(0, idArray.GetNumberOfTuples() - 1)

    self.logic.applyPolyMask(self.polyData)
    self.resetPolyData()

  def createPolyData(self):
    """make an empty single-polyline polydata"""

    polyData = vtk.vtkPolyData()
    polyData.SetPoints(self.xyPoints)

    lines = vtk.vtkCellArray()
    polyData.SetLines(lines)
    idArray = lines.GetData()
    idArray.Reset()
    idArray.InsertNextTuple1(0)

    polygons = vtk.vtkCellArray()
    polyData.SetPolys(polygons)
    idArray = polygons.GetData()
    idArray.Reset()
    idArray.InsertNextTuple1(0)

    return polyData


  def resetPolyData(self):
    """return the polyline to initial state with no points"""
    lines = self.polyData.GetLines()
    idArray = lines.GetData()
    idArray.Reset()
    idArray.InsertNextTuple1(0)
    self.xyPoints.Reset()
    self.rasPoints.Reset()
    lines.SetNumberOfCells(0)
    self.activeSlice = None

  def addPoint(self,ras):
    """add a world space point to the current outline"""
    # store active slice when first point is added
    sliceLogic = self.sliceWidget.sliceLogic()
    currentSlice = sliceLogic.GetSliceOffset()
    if not self.activeSlice:
      self.activeSlice = currentSlice
      self.setLineMode("solid")
    
    # don't allow adding points on except on the active slice (where
    # first point was laid down)
    if self.activeSlice != currentSlice: return

    # keep track of node state (in case of pan/zoom)
    sliceNode = sliceLogic.GetSliceNode()
    self.lastInsertSliceNodeMTime = sliceNode.GetMTime()

    p = self.rasPoints.InsertNextPoint(ras)
    lines = self.polyData.GetLines()
    idArray = lines.GetData()
    idArray.InsertNextTuple1(p)
    idArray.SetTuple1(0, idArray.GetNumberOfTuples()-1)
    lines.SetNumberOfCells(1)

  def deleteLastPoint():
    """unwind through addPoint list back to empy polydata"""

    pcount = self.rasPoints.GetNumberOfPoints()
    if pcount <= 0: return

    pcount = pcount - 1
    self.rasPoints.SetNumberOfPoints(pcount)

    lines = self.polyData.GetLines()
    idArray = lines.GetData()
    idArray.SetTuple1(0, pcount)
    idArray.SetNumberOfTuples(pcount+1)

    self.positionActors()

#
# DrawEffectLogic
#
 
class DrawEffectLogic(LabelEffect.LabelEffectLogic):
  """
  This class contains helper methods for a given effect
  type.  It can be instanced as needed by an DrawEffectTool
  or DrawEffectOptions instance in order to compute intermediate
  results (say, for user feedback) or to implement the final 
  segmentation editing operation.  This class is split
  from the DrawEffectTool so that the operations can be used
  by other code without the need for a view context.
  """

  def __init__(self,sliceLogic):
    super(DrawEffectLogic,self).__init__(sliceLogic)


#
# The DrawEffect class definition 
#

class DrawEffect(LabelEffect.LabelEffect):
  """Organizes the Options, Tool, and Logic classes into a single instance
  that can be managed by the EditBox
  """

  def __init__(self):
    # name is used to define the name of the icon image resource (e.g. DrawEffect.png)
    self.name = "DrawEffect"
    # tool tip is displayed on mouse hover
    self.toolTip = "Draw: circular paint brush for label map editing"

    self.options = DrawEffectOptions
    self.tool = DrawEffectTool
    self.logic = DrawEffectLogic

""" Test:

sw = slicer.app.layoutManager().sliceWidget('Red')
import EditorLib
pet = EditorLib.DrawEffectTool(sw)

"""
