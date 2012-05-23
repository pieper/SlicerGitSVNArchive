import os
from __main__ import vtk
from __main__ import qt
from __main__ import ctk
from __main__ import slicer
from EditOptions import EditOptions
import EditUtil
import Effect


#########################################################
#
# 
comment = """

  LabelEffect is a subclass of Effect (for tools that plug into the 
  slicer Editor module) and a superclass for tools edit the 
  currently selected label map (i.e. for things like paint or
  draw, but not for things like make model or next fiducial).

# TODO : 
"""
#
#########################################################

#
# LabelEffectOptions - see EditOptions and Effect for superclasses
#

class LabelEffectOptions(Effect.EffectOptions):
  """ LabelEffect-specfic gui
  """

  def __init__(self, parent=0):
    super(LabelEffectOptions,self).__init__(parent)

  def __del__(self):
    super(LabelEffectOptions,self).__del__()

  def create(self):
    super(LabelEffectOptions,self).create()
    self.paintOver = qt.QCheckBox("Paint Over", self.frame)
    self.paintOver.setToolTip("Allow effect to overwrite non-zero labels.")
    self.frame.layout().addWidget(self.paintOver)
    self.widgets.append(self.paintOver)

    self.thresholdPaint = qt.QCheckBox("Threshold Paint", self.frame)
    self.thresholdPaint.setToolTip("Enable/Disable threshold mode for labeling.")
    self.frame.layout().addWidget(self.thresholdPaint)
    self.widgets.append(self.thresholdPaint)

    self.thresholdLabel = qt.QLabel("Threshold", self.frame)
    self.thresholdLabel.setToolTip("In threshold mode, the label will only be set if the background value is within this range.")
    self.frame.layout().addWidget(self.thresholdLabel)
    self.widgets.append(self.thresholdLabel)
    self.threshold = ctk.ctkRangeWidget(self.frame)
    self.threshold.spinBoxAlignment = 0xff # put enties on top
    self.threshold.singleStep = 0.01
    self.setRangeWidgetToBackgroundRange(self.threshold)
    self.frame.layout().addWidget(self.threshold)
    self.widgets.append(self.threshold)

    self.connections.append( (self.paintOver, "clicked()", self.updateMRMLFromGUI ) )
    self.connections.append( (self.thresholdPaint, "clicked()", self.updateMRMLFromGUI ) )
    self.connections.append( (self.threshold, "valuesChanged(double,double)", self.onThresholdValuesChange ) )

  def destroy(self):
    super(LabelEffectOptions,self).destroy()

  def updateParameterNode(self, caller, event):
    """
    note: this method needs to be implemented exactly as
    defined in the leaf classes in EditOptions.py
    in each leaf subclass so that "self" in the observer
    is of the correct type """
    pass

  def setMRMLDefaults(self):
    super(LabelEffectOptions,self).setMRMLDefaults()
    disableState = self.parameterNode.GetDisableModifiedEvent()
    self.parameterNode.SetDisableModifiedEvent(1)
    defaults = (
      ("paintOver", "1"),
      ("paintThreshold", "0"),
      ("paintThresholdMin", "0"),
      ("paintThresholdMax", "1000"),
    )
    for d in defaults:
      param = "LabelEffect,"+d[0]
      pvalue = self.parameterNode.GetParameter(param)
      if pvalue == '':
        self.parameterNode.SetParameter(param, d[1])
    self.parameterNode.SetDisableModifiedEvent(disableState)

  def updateGUIFromMRML(self,caller,event):
    # first, check that parameter node has proper defaults for your effect
    # then, call superclass
    # then, update yourself from MRML parameter node
    # - follow pattern in EditOptions leaf classes
    params = ("paintOver", "paintThreshold", "paintThresholdMin", "paintThresholdMax")
    for p in params:
      if self.parameterNode.GetParameter("LabelEffect,"+p) == '':
        # don't update if the parameter node has not got all values yet
        return
    super(LabelEffectOptions,self).updateGUIFromMRML(caller,event)
    self.disconnectWidgets()
    self.paintOver.setChecked( 
                int(self.parameterNode.GetParameter("LabelEffect,paintOver")) )
    self.thresholdPaint.setChecked( 
                int(self.parameterNode.GetParameter("LabelEffect,paintThreshold")) )
    self.threshold.setMinimumValue( 
                float(self.parameterNode.GetParameter("LabelEffect,paintThresholdMin")) )
    self.threshold.setMaximumValue( 
                float(self.parameterNode.GetParameter("LabelEffect,paintThresholdMax")) )
    self.thresholdLabel.setHidden( not self.thresholdPaint.checked )
    self.threshold.setHidden( not self.thresholdPaint.checked )
    self.threshold.setEnabled( self.thresholdPaint.checked )
    self.connectWidgets()

  def onThresholdValuesChange(self,min,max):
    self.updateMRMLFromGUI()

  def updateMRMLFromGUI(self):
    disableState = self.parameterNode.GetDisableModifiedEvent()
    self.parameterNode.SetDisableModifiedEvent(1)
    super(LabelEffectOptions,self).updateMRMLFromGUI()
    if self.paintOver.checked:
      self.parameterNode.SetParameter( "LabelEffect,paintOver", "1" )
    else:
      self.parameterNode.SetParameter( "LabelEffect,paintOver", "0" )
    if self.thresholdPaint.checked:
      self.parameterNode.SetParameter( "LabelEffect,paintThreshold", "1" )
    else:
      self.parameterNode.SetParameter( "LabelEffect,paintThreshold", "0" )
    self.parameterNode.SetParameter( 
                "LabelEffect,paintThresholdMin", str(self.threshold.minimumValue) )
    self.parameterNode.SetParameter( 
                "LabelEffect,paintThresholdMax", str(self.threshold.maximumValue) )
    self.parameterNode.SetDisableModifiedEvent(disableState)
    if not disableState:
      self.parameterNode.InvokePendingModifiedEvent()

#
# LabelEffectTool
#
 
class LabelEffectTool(Effect.EffectTool):
  """
  One instance of this will be created per-view when the effect
  is selected.  It is responsible for implementing feedback and
  label map changes in response to user input.
  This class observes the editor parameter node to configure itself
  and queries the current view for background and label volume
  nodes to operate on.
  """

  def __init__(self,sliceWidget, threeDWidget=None):
    super(LabelEffectTool,self).__init__(sliceWidget, threeDWidget)
    self.rotateSliceToImage()

  def cleanup(self):
    super(LabelEffectTool,self).cleanup()

  def rotateSliceToImage(self):
    """adjusts the slice node to align with the 
      native space of the image data so that paint
      operations can happen cleanly between image
      space and screen space"""

    sliceLogic = self.sliceWidget.sliceLogic()
    sliceNode = self.sliceWidget.mrmlSliceNode()
    volumeNode = sliceLogic.GetBackgroundLayer().GetVolumeNode()

    sliceNode.RotateToVolumePlane(volumeNode)
    # make sure the slice plane does not lie on an index boundary 
    # - (to avoid rounding issues)
    sliceLogic.SnapSliceOffsetToIJK()
    sliceNode.UpdateMatrices()


#
# LabelEffectLogic
#
 
class LabelEffectLogic(Effect.EffectLogic):
  """
  This class contains helper methods for a given effect
  type.  It can be instanced as needed by an LabelEffectTool
  or LabelEffectOptions instance in order to compute intermediate
  results (say, for user feedback) or to implement the final 
  segmentation editing operation.  This class is split
  from the LabelEffectTool so that the operations can be used
  by other code without the need for a view context.
  """

  def __init__(self,sliceLogic):
    super(LabelEffectLogic,self).__init__(sliceLogic)
    self.paintThreshold = 0
    self.paintThresholdMin = 1
    self.paintThresholdMax = 1
    self.paintOver = 1
    self.extractImage = None
    self.painter = slicer.vtkImageSlicePaint()


  def makeMaskImage(self,polyData):
    """
    Create a screen space (2D) mask image for the given
    polydata.

    Need to know the mapping from RAS into polygon space
    so the painter can use this as a mask
    - need the bounds in RAS space
    - need to get an IJKToRAS for just the mask area
    - directions are the XYToRAS for this slice
    - origin is the lower left of the polygon bounds
    - TODO: need to account for the boundary pixels
    
     Note: uses the slicer2-based vtkImageFillROI filter
    """
    labelLogic = self.sliceLogic.GetLabelLayer()
    sliceNode = self.sliceLogic.GetSliceNode()
    maskIJKToRAS = vtk.vtkMatrix4x4()
    maskIJKToRAS.DeepCopy(sliceNode.GetXYToRAS())
    polyData.GetPoints().Modified()
    bounds = polyData.GetBounds()
    xlo = bounds[0] - 1
    xhi = bounds[1]
    ylo = bounds[2] - 1
    yhi = bounds[3]
    originRAS = self.xyToRAS((xlo,ylo))
    maskIJKToRAS.SetElement( 0, 3, originRAS[0] )
    maskIJKToRAS.SetElement( 1, 3, originRAS[1] )
    maskIJKToRAS.SetElement( 2, 3, originRAS[2] )

    #
    # get a good size for the draw buffer 
    # - needs to include the full region of the polygon
    # - plus a little extra 
    #
    # round to int and add extra pixel for both sides
    # -- TODO: figure out why we need to add buffer pixels on each 
    #    side for the width in order to end up with a single extra
    #    pixel in the rasterized image map.  Probably has to 
    #    do with how boundary conditions are handled in the filler
    w = int(xhi - xlo) + 32
    h = int(yhi - ylo) + 32

    imageData = vtk.vtkImageData()
    imageData.SetDimensions( w, h, 1 )

    labelNode = labelLogic.GetVolumeNode()
    if not labelNode: return
    labelImage = labelNode.GetImageData()
    if not labelImage: return
    imageData.SetScalarType(labelImage.GetScalarType()) 
    imageData.AllocateScalars()

    #
    # move the points so the lower left corner of the 
    # bounding box is at 1, 1 (to avoid clipping)
    #
    translate = vtk.vtkTransform()
    translate.Translate( -1. * xlo, -1. * ylo, 0)
    drawPoints = vtk.vtkPoints()
    drawPoints.Reset()
    translate.TransformPoints( polyData.GetPoints(), drawPoints )
    drawPoints.Modified()

    fill = slicer.vtkImageFillROI()
    fill.SetInput(imageData)
    fill.SetValue(1)
    fill.SetPoints(drawPoints)
    fill.GetOutput().Update()

    mask = vtk.vtkImageData()
    mask.DeepCopy(fill.GetOutput())

    return [maskIJKToRAS, mask]

  def applyThreeDPolyMask(self,polyData,camera,size,debugGeometry=True):
    """
    rasterize a polyData (closed list of points) 
    into the label map layer by tracing along a path
    defined by the given camera
    """

    import numpy
    import numpy.linalg
    
    # get the background and label to operate on
    backgroundLogic = self.sliceLogic.GetBackgroundLayer()
    backgroundNode = backgroundLogic.GetVolumeNode()
    if not backgroundNode: return
    backgroundImage = backgroundNode.GetImageData()
    if not backgroundImage: return
    labelLogic = self.sliceLogic.GetLabelLayer()
    labelNode = labelLogic.GetVolumeNode()
    if not labelNode: return
    labelImage = labelNode.GetImageData()
    if not labelImage: return

    # get a rasterized mask the size of the view
    imageData = vtk.vtkImageData()
    imageData.SetDimensions( size + (1,) )
    imageData.SetScalarType(labelImage.GetScalarType()) 
    imageData.AllocateScalars()
    fill = slicer.vtkImageFillROI()
    fill.SetInput(imageData)
    fill.SetValue(1)
    fill.SetPoints(polyData.GetPoints())
    fill.GetOutput().Update()
    mask = vtk.vtkImageData()
    mask.DeepCopy(fill.GetOutput())

    # get the key camera values as numpy arrays for convenience
    # TODO: make a python helper class for cameras
    position = numpy.array(camera.GetPosition())
    focalPoint = numpy.array(camera.GetFocalPoint())
    viewDistance = numpy.linalg.norm(focalPoint - position)
    viewDirection = (focalPoint - position) / viewDistance
    viewPlaneNormal = numpy.array(camera.GetViewPlaneNormal())
    viewUp = numpy.array(camera.GetViewUp())
    viewAngle = camera.GetViewAngle()
    tanHalfViewAngle = numpy.tan(numpy.radians(viewAngle/2.))
    viewRight = numpy.cross(viewUp,viewDirection)
    nearDistance = farDistance = viewDistance

    # find the near and far points of the volume
    ijkToRAS = vtk.vtkMatrix4x4()
    labelNode.GetIJKToRASMatrix(ijkToRAS)
    transformNode = labelNode.GetParentTransformNode()
    if transformNode:
      if transformNode.IsTransformToWorldLinear():
        rasToRAS = vtk.vtkMatrix4x4()
        transformNode.GetMatrixTransformToWorld(rasToRAS)
        rasToRAS.Multiply4x4(rasToRAS, ijkToRAS, ijkToRAS)
      else:
        print ("Cannot handle non-linear transforms")
        return
    dimensions = labelImage.GetDimensions()
    for column in (0,dimensions[0]):
      for row in (0,dimensions[1]):
        for slice_ in (0,dimensions[2]):
          corner = ijkToRAS.MultiplyPoint( (column, row, slice_, 1) )[:3]
          camToCorner = corner - position
          print("camToCorner is ", camToCorner)
          toCornerOnVDir = viewDirection * numpy.dot(viewDirection,camToCorner)
          print("toCornerOnVDir is ", toCornerOnVDir)
          dist = numpy.linalg.norm(toCornerOnVDir)
          print("dist to corner", corner, " is ", dist)
          nearDistance = min(nearDistance,dist)
          farDistance = max(farDistance,dist)
          if debugGeometry:
            fidNode = slicer.vtkMRMLAnnotationFiducialNode()
            fidNode.SetFiducialCoordinates(corner)
            fidNode.Initialize(slicer.mrmlScene)
            fidNode.SetName("vol corner")
            fidNode.SetLocked(1)

    maskIJKToRAS = vtk.vtkMatrix4x4()
    for row in xrange(3):
      # where to move in RAS while moving along a row of the mask
      maskIJKToRAS.SetElement(row,0, viewRight[row])
      # where to move in RAS while moving along a column
      maskIJKToRAS.SetElement(row,1, -viewUp[row])
      # where to move in RAS while moving along a slice (not used)
      maskIJKToRAS.SetElement(row,2, viewDirection[row])

    # march through the volume applying the label mask
    step = min(labelNode.GetSpacing())
    if nearDistance > farDistance or step <= 0:
      print ("Cannot apply")
      print ("nearDistance %d farDistance %d step %d" % (nearDistance, farDistance, step) )
      return
    print ("nearDistance %d farDistance %d step %d" % (nearDistance, farDistance, step) )
    dist = nearDistance
    #while dist < farDistance:
    halfDist = (nearDistance + farDistance)/2.
    for dist in (nearDistance, halfDist, farDistance):
      in_ = viewDirection * dist
      right = viewRight * tanHalfViewAngle * dist
      up = viewUp * tanHalfViewAngle * dist 
      print("drawing at distance ", dist, " RAS ", position + in_)
      print("in, right, up", (in_, right, up))
      topLeftRAS = position + in_ - right + up
      topRightRAS = position + in_ + right + up
      bottomLeftRAS = position + in_ - right - up
      bottomRightRAS = position + in_ + right - up
      cornersRAS = (topLeftRAS, topRightRAS, bottomLeftRAS, bottomRightRAS)
      for row in xrange(3):
        # position of the top left corner of the mask
        maskIJKToRAS.SetElement(row,3, topLeftRAS[row])

      #now, apply the mask at this plane
      print ("apply: ", mask, maskIJKToRAS, cornersRAS )
      self.paintImageMask( mask, maskIJKToRAS, cornersRAS )

      if debugGeometry:
        points = ( ("topLeftRAS", topLeftRAS), ("topRightRAS", topRightRAS), 
            ("bottomRightRAS", bottomRightRAS), ("bottomLeftRAS", bottomLeftRAS))
        pointIndex = 0
        for name,point in points:
          fidNode = slicer.vtkMRMLAnnotationFiducialNode()
          fidNode.SetFiducialCoordinates(point)
          fidNode.Initialize(slicer.mrmlScene)
          fidNode.SetName(name)
          fidNode.SetLocked(1)
          rulerNode = slicer.vtkMRMLAnnotationRulerNode()
          rulerNode.SetPosition1(point)
          rulerNode.SetPosition2(points[(pointIndex+1) % len(points)][1])
          rulerNode.Initialize(slicer.mrmlScene)
          rulerNode.SetName("edge")
          rulerNode.SetLocked(1)
          pointIndex += 1

      dist += step


  def applyPolyMask(self,polyData):
    """
    rasterize a polyData (closed list of points) 
    into the label map layer
    - points are specified in current XY space
    """

    labelLogic = self.sliceLogic.GetLabelLayer()
    sliceNode = self.sliceLogic.GetSliceNode()
    labelNode = labelLogic.GetVolumeNode()
    if not sliceNode or not labelNode: return

    maskIJKToRAS, mask = self.makeMaskImage(polyData)

    polyData.GetPoints().Modified()
    bounds = polyData.GetBounds()

    self.applyImageMask(maskIJKToRAS, mask, bounds)

  def applyImageMask(self, maskIJKToRAS, mask, bounds):
    """
    apply a pre-rasterized image to the current label layer
    - maskIJKToRAS tells the mapping from image pixels to RAS
    - mask is a vtkImageData
    - bounds are the xy extents of the mask (zlo and zhi ignored)
    """
    backgroundLogic = self.sliceLogic.GetBackgroundLayer()
    backgroundNode = backgroundLogic.GetVolumeNode()
    if not backgroundNode: return
    backgroundImage = backgroundNode.GetImageData()
    if not backgroundImage: return
    labelLogic = self.sliceLogic.GetLabelLayer()
    labelNode = labelLogic.GetVolumeNode()
    if not labelNode: return
    labelImage = labelNode.GetImageData()
    if not labelImage: return
    
    #
    # at this point, the mask vtkImageData contains a rasterized
    # version of the polygon and now needs to be added to the label
    # image
    #

    #
    # get the mask bounding box in ijk coordinates
    # - get the xy bounds
    # - transform to ijk
    # - clamp the bounds to the dimensions of the label image
    #

    xlo, xhi, ylo, yhi, zlo, zhi = bounds
    sliceNode = self.sliceLogic.GetSliceNode()
    xyToRAS = sliceNode.GetXYToRAS()
    tlRAS = xyToRAS.MultiplyPoint( (xlo, yhi, 0, 1) )[:3]
    trRAS = xyToRAS.MultiplyPoint( (xhi, yhi, 0, 1) )[:3]
    blRAS = xyToRAS.MultiplyPoint( (xlo, ylo, 0, 1) )[:3]
    brRAS = xyToRAS.MultiplyPoint( (xhi, ylo, 0, 1) )[:3]
    cornersRAS = (tlRAS,trRAS,blRAS,brRAS)

    self.paintImageMask( mask, maskIJKToRAS, cornersRAS )

  def paintImageMask(self,mask,maskIJKToRAS,cornersRAS):
    """
    apply the given mask image using a painter to the current
    label volume in the context of the current background volume.

    mask : a vtkImageData containing the mask to apply
    maskIJKToRAS : a vtkMatrix4x4 defining the transform from
     pixel coordinates of the mask to world space
    cornersRAS : the world space corners of the mask to apply
      (in order of (tl, tr, bl, br))
    """

    labelLogic = self.sliceLogic.GetLabelLayer()
    labelNode = labelLogic.GetVolumeNode()
    labelImage = labelNode.GetImageData()
    backgroundLogic = self.sliceLogic.GetLabelLayer()
    backgroundNode = backgroundLogic.GetVolumeNode()
    backgroundImage = backgroundNode.GetImageData()

    # store a backup copy of the label map for undo
    # (this happens in it's own thread, so it is cheap)
    if self.undoRedo:
      self.undoRedo.saveState()

    #
    # get the ijk to ras matrices including transforms
    # (use the maskToRAS calculated above)
    #

    backgroundIJKToRAS = vtk.vtkMatrix4x4()
    labelIJKToRAS = vtk.vtkMatrix4x4()
    labelRASToIJK = vtk.vtkMatrix4x4()

    sets = ( (backgroundNode, backgroundIJKToRAS), (labelNode, labelIJKToRAS) )
    for node,ijkToRAS in sets:
      node.GetIJKToRASMatrix(ijkToRAS)
      transformNode = node.GetParentTransformNode()
      if transformNode:
        if transformNode.IsTransformToWorldLinear():
          rasToRAS = vtk.vtkMatrix4x4()
          transformNode.GetMatrixTransformToWorld(rasToRAS)
          rasToRAS.Multiply4x4(rasToRAS, ijkToRAS, ijkToRAS)
        else:
          print ("Cannot handle non-linear transforms")
          return
    labelRASToIJK.DeepCopy(labelIJKToRAS)
    labelRASToIJK.Invert()

    #
    # do the clamping of the four corners in IJK space of label
    #
    tlRAS,trRAS,blRAS,brRAS = cornersRAS
    dims = labelImage.GetDimensions()
    tl = [0,] * 3
    tr = [0,] * 3
    bl = [0,] * 3
    br = [0,] * 3
    corners = ((tlRAS, tl),(trRAS, tr),(blRAS, bl),(brRAS, br))
    for cornerRAS,clampedCorner in corners:
      cornerIJK = labelRASToIJK.MultiplyPoint( list(cornerRAS) + [1,] )[:3]
      for d in xrange(3):
        clamped = int(round(cornerIJK[d]))
        if clamped < 0: clamped = 0
        if clamped >= dims[d]: clamped = dims[d]-1
        clampedCorner[d] = clamped

    print("tl", tl)
    print("tr", tr)
    print("bl", bl)
    print("br", br)

    #
    # create an exract image for undo if it doesn't exist yet.
    # and extract parameters
    #

    parameterNode = self.editUtil.getParameterNode()
    paintLabel = int(parameterNode.GetParameter("label"))
    paintOver = int(parameterNode.GetParameter("LabelEffect,paintOver"))
    paintThreshold = int(parameterNode.GetParameter("LabelEffect,paintThreshold"))
    paintThresholdMin = float(
        parameterNode.GetParameter("LabelEffect,paintThresholdMin"))
    paintThresholdMax = float(
        parameterNode.GetParameter("LabelEffect,paintThresholdMax"))

    #
    # set up the painter class and let 'r rip!
    #
    self.painter.SetBackgroundImage( backgroundImage )
    self.painter.SetBackgroundIJKToWorld( backgroundIJKToRAS )
    self.painter.SetWorkingImage( labelImage )
    self.painter.SetWorkingIJKToWorld( labelIJKToRAS )
    self.painter.SetMaskImage( mask )
    self.painter.SetReplaceImage(None)
    self.painter.SetMaskIJKToWorld( maskIJKToRAS )
    self.painter.SetTopLeft(tl)
    self.painter.SetTopRight(tr)
    self.painter.SetBottomLeft(bl)
    self.painter.SetBottomRight(br)

    self.painter.SetPaintLabel( paintLabel )
    self.painter.SetPaintOver( paintOver )
    self.painter.SetThresholdPaint( paintThreshold )
    self.painter.SetThresholdPaintRange( paintThresholdMin, paintThresholdMax )

    self.painter.Paint()

    labelNode.SetModifiedSinceRead(1)
    labelNode.Modified()

  def sliceIJKPlane(self):
    """ Return a code indicating which plane of IJK
    space corresponds to the current slice plane orientation.
    Values are 'IJ', 'IK', 'JK', or None.
    This is useful for algorithms like LevelTracing that operate
    in pixel space."""
    offset = max(self.sliceLogic.GetSliceNode().GetDimensions())
    i0,j0,k0 = self.backgroundXYToIJK( (0,0) )
    i1,j1,k1 = self.backgroundXYToIJK( (offset,offset) )
    if i0 == i1 and j0 == j1 and k0 == k1:
      return None
    if i0 == i1:
      return 'JK'
    if j0 == j1:
      return 'IK'
    if k0 == k1:
      return 'IJ'
    return None

#
# The LabelEffect class definition 
#

class LabelEffect(Effect.Effect):
  """Organizes the Options, Tool, and Logic classes into a single instance
  that can be managed by the EditBox
  """

  def __init__(self):
    # name is used to define the name of the icon image resource (e.g. LabelEffect.png)
    self.name = "LabelEffect"
    # tool tip is displayed on mouse hover
    self.toolTip = "LabelEffect: Generic abstract labeling effect - not meant to be instanced"

    self.options = LabelEffectOptions
    self.tool = LabelEffectTool
    self.logic = LabelEffectLogic
