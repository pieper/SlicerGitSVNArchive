import os
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

    self.paintOver.connect( "clicked()", self.updateMRMLFromGUI )
    self.thresholdPaint.connect( "clicked()", self.updateMRMLFromGUI )
    self.threshold.connect( "valuesChanged(double,double)", self.onThresholdValuesChange )

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
    self.updatingGUI = True
    super(LabelEffectOptions,self).updateGUIFromMRML(caller,event)
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
    self.updatingGUI = False

  def onThresholdValuesChange(self,min,max):
    self.updateMRMLFromGUI()

  def updateMRMLFromGUI(self):
    if self.updatingGUI:
      return
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

  def __init__(self,sliceWidget):
    super(LabelEffectTool,self).__init__(sliceWidget)
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

  def __init__(self):
    super(LabelEffectLogic,self).__init__()
    self.paintThreshold = 0
    self.paintThresholdMin = 1
    self.paintThresholdMax = 1
    self.paintOver = 1
    self.painter = slicer.vtkImageSlicePaint()


  def makeMaskImage(self,polyData):
    """
    Need to know the mapping from RAS into polygon space
    so the painter can use this as a mask
    - need the bounds in RAS space
    - need to get an IJKToRAS for just the mask area
    - directions are the XYToRAS for this slice
    - origin is the lower left of the polygon bounds
    - TODO: need to account for the boundary pixels
    
     ps uses the slicer2-based vtkImageFillROI filter
    """
    set maskIJKToRAS [vtkMatrix4x4 New]
    $maskIJKToRAS DeepCopy [$_sliceNode GetXYToRAS]
    [$polyData GetPoints] Modified
    set bounds [$polyData GetBounds]
    foreach {xlo xhi ylo yhi zlo zhi} $bounds {}
    set xlo [expr $xlo - 1]
    set ylo [expr $ylo - 1]
    set originRAS [$this xyToRAS "$xlo $ylo"]
    $maskIJKToRAS SetElement 0 3  [lindex $originRAS 0]
    $maskIJKToRAS SetElement 1 3  [lindex $originRAS 1]
    $maskIJKToRAS SetElement 2 3  [lindex $originRAS 2]

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
    set w [expr int($xhi - $xlo) + 32]
    set h [expr int($yhi - $ylo) + 32]

    set imageData [vtkImageData New]
    $imageData SetDimensions $w $h 1

    if { $_layers(label,image) != "" } {
      $imageData SetScalarType [$_layers(label,image) GetScalarType]
    }
    $imageData AllocateScalars

    #
    # move the points so the lower left corner of the 
    # bounding box is at 1, 1 (to avoid clipping)
    #
    set translate [vtkTransform New]
    $translate Translate [expr -1. * $xlo] [expr -1. * $ylo] 0
    set drawPoints [vtkPoints New]
    $drawPoints Reset
    $translate TransformPoints [$polyData GetPoints] $drawPoints
    $translate Delete
    $drawPoints Modified

    set fill [vtkImageFillROI New]
    $fill SetInput $imageData
    $fill SetValue 1
    $fill SetPoints $drawPoints
    [$fill GetOutput] Update

    set mask [vtkImageData New]
    $mask DeepCopy [$fill GetOutput]

    if { $polygonDebugViewer } {
      #
      # make a little preview window for debugging pleasure
      #
      catch "viewer Delete"
      catch "viewerImage Delete"
      vtkImageViewer viewer
      vtkImageData viewerImage
      viewerImage DeepCopy [$fill GetOutput]
      viewer SetInput viewerImage
      viewer SetColorWindow 2
      viewer SetColorLevel 1
      viewer Render
    }


    #
    # clean up our local class instances
    #
    $fill Delete
    $imageData Delete
    $drawPoints Delete

    return [list $maskIJKToRAS $mask]
  }
  """

  def applyPolyMask(self,polyData):
    """
    rasterize a polyData (closed list of points) 
    into the label map layer
    - points are specified in current XY space
    """

    """
      foreach {x y} [$_interactor GetEventPosition] {}
      $this queryLayers $x $y

      if { $_layers(label,node) == "" } {
        # if there's no label, we can't draw
        return
      }

      set maskResult [$this makeMaskImage $polyData]
      foreach {maskIJKToRAS mask} $maskResult {}

      [$polyData GetPoints] Modified
      set bounds [$polyData GetBounds]

      $this applyImageMask $maskIJKToRAS $mask $bounds

    }
    """

  def applyImageMask(self, maskIJKToRAS, mask, bounds):
    """
    apply a pre-rasterized image to the current label layer
    - maskIJKToRAS tells the mapping from image pixels to RAS
    - mask is a vtkImageData
    - bounds are the xy extents of the mask (zlo and zhi ignored)
    """
    
    itcl::body Labeler::applyImageMask { maskIJKToRAS mask bounds } {

      #
      # at this point, the mask vtkImageData contains a rasterized
      # version of the polygon and now needs to be added to the label
      # image
      #
      
      # store a backup copy of the label map for undo
      # (this happens in it's own thread, so it is cheap)
      EditorStoreCheckPoint $_layers(label,node)

      #
      # get the brush bounding box in ijk coordinates
      # - get the xy bounds
      # - transform to ijk
      # - clamp the bounds to the dimensions of the label image
      #

      foreach {xlo xhi ylo yhi zlo zhi} $bounds {}
      set xyToIJK [[$_layers(label,logic) GetXYToIJKTransform] GetMatrix]
      set tlIJK [$xyToIJK MultiplyPoint $xlo $yhi 0 1]
      set trIJK [$xyToIJK MultiplyPoint $xhi $yhi 0 1]
      set blIJK [$xyToIJK MultiplyPoint $xlo $ylo 0 1]
      set brIJK [$xyToIJK MultiplyPoint $xhi $ylo 0 1]

      # do the clamping
      set dims [$_layers(label,image) GetDimensions]
      foreach v {i j k} c [lrange $tlIJK 0 2] d $dims {
        set tl($v) [expr int(round($c))]
        if { $tl($v) < 0 } { set tl($v) 0 }
        if { $tl($v) >= $d } { set tl($v) [expr $d - 1] }
      }
      foreach v {i j k} c [lrange $trIJK 0 2] d $dims {
        set tr($v) [expr int(round($c))]
        if { $tr($v) < 0 } { set tr($v) 0 }
        if { $tr($v) >= $d } { set tr($v) [expr $d - 1] }
      }
      foreach v {i j k} c [lrange $blIJK 0 2] d $dims {
        set bl($v) [expr int(round($c))]
        if { $bl($v) < 0 } { set bl($v) 0 }
        if { $bl($v) >= $d } { set bl($v) [expr $d - 1] }
      }
      foreach v {i j k} c [lrange $brIJK 0 2] d $dims {
        set br($v) [expr int(round($c))]
        if { $br($v) < 0 } { set br($v) 0 }
        if { $br($v) >= $d } { set br($v) [expr $d - 1] }
      }


      #
      # get the ijk to ras matrices 
      # (use the maskToRAS calculated above)
      #


      set backgroundIJKToRAS [vtkMatrix4x4 New]
      set labelIJKToRAS [vtkMatrix4x4 New]
      foreach layer {background label} {
        set ijkToRAS ${layer}IJKToRAS
        $_layers($layer,node) GetIJKToRASMatrix [set $ijkToRAS]
        set transformNode [$_layers($layer,node) GetParentTransformNode]
        if { $transformNode != "" } {
          if { [$transformNode IsTransformToWorldLinear] } {
            set rasToRAS [vtkMatrix4x4 New]
            $transformNode GetMatrixTransformToWorld $rasToRAS
            $rasToRAS Multiply4x4 $rasToRAS [set $ijkToRAS] [set $ijkToRAS]
            $rasToRAS Delete
          } else {
            error "Cannot handle non-linear transforms"
          }
        }
      }


      #
      # create an exract image for undo if it doesn't exist yet
      #
      if { ![info exists o(extractImage)] } {
        set o(extractImage) [vtkNew vtkImageData]
      }

      #
      # set up the painter class and let 'r rip!
      #
      $o(painter) SetBackgroundImage [$this getInputBackground]
      $o(painter) SetBackgroundIJKToWorld $backgroundIJKToRAS
      $o(painter) SetWorkingImage [$this getInputLabel]
      $o(painter) SetWorkingIJKToWorld $labelIJKToRAS
      $o(painter) SetMaskImage $mask
      $o(painter) SetExtractImage $o(extractImage)
      $o(painter) SetReplaceImage ""
      $o(painter) SetMaskIJKToWorld $maskIJKToRAS
      $o(painter) SetTopLeft $tl(i) $tl(j) $tl(k)
      $o(painter) SetTopRight $tr(i) $tr(j) $tr(k)
      $o(painter) SetBottomLeft $bl(i) $bl(j) $bl(k)
      $o(painter) SetBottomRight $br(i) $br(j) $br(k)
      $o(painter) SetPaintLabel [EditorGetPaintLabel]
      $o(painter) SetPaintOver $paintOver
      $o(painter) SetThresholdPaint $paintThreshold
      $o(painter) SetThresholdPaintRange $paintThresholdMin $paintThresholdMax

      $o(painter) Paint

      $labelIJKToRAS Delete
      $backgroundIJKToRAS Delete
      $maskIJKToRAS Delete
      $mask Delete

      # TODO: workaround for new pipeline in slicer4
      # - editing image data of the calling modified on the node
      #   does not pull the pipeline chain
      # - so we trick it by changing the image data first
      $_layers(label,node) SetModifiedSinceRead 1
      set workaround 1
      if { $workaround } {
        if { ![info exists o(tempImageData)] } {
          set o(tempImageData) [vtkNew vtkImageData]
        }
        set imageData [$_layers(label,node) GetImageData]
        $_layers(label,node) SetAndObserveImageData $o(tempImageData)
        $_layers(label,node) SetAndObserveImageData $imageData
      } else {
        $_layers(label,node) Modified
      }

      return
    }
    """


  def undoLastApply(self):
    """
    # use the 'save under' information from last paint apply
    # to restore the original value of the working volume
    # - be careful can only call this after when the painter class
    #   is valid (e.g. after an apply but before changing any of the volumes)
    #   it should be crash-proof in any case, but may generated warnings
    # - if extract image doesn't exist, failes silently
    itcl::body Labeler::undoLastApply { } {
      if { [info exists o(extractImage)] } {
        $o(painter) SetReplaceImage $o(extractImage)
        $o(painter) Paint
      }
    }
    """


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
