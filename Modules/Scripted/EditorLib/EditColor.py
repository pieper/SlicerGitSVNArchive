import slicer
import qt
import vtk
# from ctk import ctkCollapsibleButton
import ColorBox
from EditUtil import EditUtil
from slicer.util import VTKObservationMixin

__all__ = ['EditColor']

#########################################################
#
#
comment = """

  EditColor is a wrapper around a set of Qt widgets and other
  structures to manage the current paint color

# TODO :
"""
#
#########################################################

class EditColor(VTKObservationMixin):

  def __init__(self, parent=0, parameter='label',colorNode=None):
    VTKObservationMixin.__init__(self)
    self.parameterNode = None
    self.parameterNodeTag = None
    self.parameter = parameter
    self.colorBox = None
    self.colorNode = colorNode
    if parent == 0:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
      self.create()
      self.parent.show()
    else:
      self.parent = parent
      self.create()

  def __del__(self):
    self.cleanup()

  def cleanup(self, QObject=None):
    if self.parameterNode:
      self.parameterNode.RemoveObserver(self.parameterNodeTag)
    self.removeObservers()

  def create(self):
    self.frame = qt.QFrame(self.parent)
    self.frame.objectName = 'EditColorFrame'
    self.frame.setLayout(qt.QVBoxLayout())
    self.parent.layout().addWidget(self.frame)

    self.colorFrame = qt.QFrame(self.frame)
    self.colorFrame.setLayout(qt.QHBoxLayout())
    self.frame.layout().addWidget(self.colorFrame)

    self.label = qt.QLabel(self.colorFrame)
    self.label.setText("Label: ")
    self.colorFrame.layout().addWidget(self.label)

    self.labelName = qt.QLabel(self.colorFrame)
    self.labelName.setText("")
    self.colorFrame.layout().addWidget(self.labelName)

    self.colorSpin = qt.QSpinBox(self.colorFrame)
    self.colorSpin.objectName = 'ColorSpinBox'
    self.colorSpin.setMaximum( 64000)
    self.colorSpin.setValue( EditUtil.getLabel() )
    self.colorSpin.setToolTip( "Click colored patch at right to bring up color selection pop up window.  Use the 'c' key to bring up color popup menu." )
    self.colorFrame.layout().addWidget(self.colorSpin)

    self.colorPatch = qt.QPushButton(self.colorFrame)
    self.colorPatch.setObjectName('ColorPatchButton')
    self.colorFrame.layout().addWidget(self.colorPatch)

    # hidden until needed terminology frames:
    self.terminologyCollapsibleButton = slicer.qMRMLCollapsibleButton(self.frame)
    self.terminologyCollapsibleButton.setText('Terminology')
    self.terminologyCollapsibleButton .setLayout(qt.QVBoxLayout())
    self.frame.layout().addWidget(self.terminologyCollapsibleButton)

    # Category section:
    self.terminologyCategoryFrame = qt.QFrame(self.terminologyCollapsibleButton)
    self.terminologyCategoryFrame.setLayout(qt.QFormLayout())
    self.terminologyCollapsibleButton.layout().addWidget(self.terminologyCategoryFrame)

    # Category
    self.terminologyCategory = qt.QLabel(self.terminologyCategoryFrame)
    self.terminologyCategory.setText("")
    # for now, read only
    # self.terminologyCategory.setReadOnly(1);
    self.terminologyCategoryFrame.layout().addRow("Category:", self.terminologyCategory )

    # Category type:
    self.terminologyCategoryType = qt.QLabel(self.terminologyCategoryFrame)
    self.terminologyCategoryType.setText("")
    # for now, read only
    # self.terminologyCategoryType.setReadOnly(1);
    self.terminologyCategoryFrame.layout().addRow("Type:", self.terminologyCategoryType )

    # Category modifier:
    self.terminologyCategoryModifier = qt.QLabel(self.terminologyCategoryFrame)
    self.terminologyCategoryModifier.setText("")
    # for now, read only
    # self.terminologyCategoryModifier.setReadOnly(1);
    self.terminologyCategoryFrame.layout().addRow("Modifier:", self.terminologyCategoryModifier )

    # Region section
    self.terminologyRegionFrame = qt.QFrame(self.terminologyCollapsibleButton)
    self.terminologyRegionFrame.setLayout(qt.QFormLayout())
    self.terminologyCollapsibleButton.layout().addWidget(self.terminologyRegionFrame)

    # Region:
    self.terminologyRegion = qt.QLabel(self.terminologyRegionFrame)
    self.terminologyRegion.setText("")
    # for now, read only
    # self.terminologyRegion.setReadOnly(1);
    self.terminologyRegionFrame.layout().addRow("Region:", self.terminologyRegion )

    # Region modifier:
    self.terminologyRegionModifier = qt.QLabel(self.terminologyRegionFrame)
    self.terminologyRegionModifier.setText("")
    # for now, read only
    # self.terminologyRegionModifier.setReadOnly(1);
    self.terminologyRegionFrame.layout().addRow("Modifier:", self.terminologyRegionModifier )

    # hide the terminology until a LUT with associated terminology is chosen
    self.hideTerminology(1)

    self.updateParameterNode(slicer.mrmlScene, vtk.vtkCommand.ModifiedEvent)
    self.updateGUIFromMRML(self.parameterNode, vtk.vtkCommand.ModifiedEvent)

    self.frame.connect( 'destroyed()', self.cleanup)
    self.colorSpin.connect( 'valueChanged(int)', self.updateMRMLFromGUI)
    self.colorPatch.connect( 'clicked()', self.showColorBox )

    # TODO: change this to look for specfic events (added, removed...)
    # but this requires being able to access events by number from wrapped code
    self.addObserver(slicer.mrmlScene, vtk.vtkCommand.ModifiedEvent, self.updateParameterNode)

  #
  # update the parameter node when the scene changes
  #
  def updateParameterNode(self, caller, event):
    #
    # observe the scene to know when to get the parameter node
    #
    parameterNode = EditUtil.getParameterNode()
    if parameterNode != self.parameterNode:
      if self.parameterNode:
        self.parameterNode.RemoveObserver(self.parameterNodeTag)
      self.parameterNode = parameterNode
      self.parameterNodeTag = self.parameterNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.updateGUIFromMRML)

  #
  # update the GUI for the given label
  #
  def updateMRMLFromGUI(self, label):
    self.parameterNode.SetParameter(self.parameter, str(label))

  #
  # update the GUI from MRML
  #
  def updateGUIFromMRML(self,caller,event):
    if self.parameterNode.GetParameter(self.parameter) == '':
      # parameter does not exist - probably intializing
      return
    label = int(self.parameterNode.GetParameter(self.parameter))

    self.colorNode = EditUtil.getColorNode()
    if self.colorNode:
      self.frame.setDisabled(0)
      self.labelName.setText( self.colorNode.GetColorName( label ) )
      lut = self.colorNode.GetLookupTable()
      rgb = lut.GetTableValue( label )
      self.colorPatch.setStyleSheet(
          "background-color: rgb(%s,%s,%s)" % (rgb[0]*255, rgb[1]*255, rgb[2]*255) )
      self.colorSpin.setMaximum( self.colorNode.GetNumberOfColors()-1 )
    else:
      self.frame.setDisabled(1)

    try:
      self.colorSpin.setValue(label)
      # check to see if there's an associated terminology with this color node
      if self.colorNode:
        terminologyName = self.colorNode.GetAttribute("TerminologyName")
        if terminologyName:
          colorLogic = slicer.modules.colors.logic()
          if colorLogic:
            # enable the terminology widgets
            self.hideTerminology(0)
            region = colorLogic.GetRegionFromLabel(label, terminologyName)
            regionModifier = colorLogic.GetRegionModifierFromLabel(label, terminologyName)
            category = colorLogic.GetCategoryFromLabel(label, terminologyName)
            categoryType = colorLogic.GetCategoryTypeFromLabel(label, terminologyName)
            categoryModifier = colorLogic.GetCategoryModifierFromLabel(label, terminologyName)
            self.terminologyRegion.setText(region)
            self.terminologyRegionModifier.setText(regionModifier)
            self.terminologyCategory.setText(category)
            self.terminologyCategoryType.setText(categoryType)
            self.terminologyCategoryModifier.setText(categoryModifier)
            # if no region information, hide the region panel
            if region is "" and regionModifier is "":
              self.terminologyRegionFrame.setHidden(1)
            else:
              self.terminologyRegionFrame.setHidden(0)
        else:
          self.hideTerminology(1)

    except ValueError:
      # TODO: why does the python class still exist if the widget is destroyed?
      # - this only happens when reloading the module.  The owner of the
      # instance is gone and the widgets are gone, but this instance still
      # has observer on the parameter node - this indicates memory leaks
      # that need to be fixed
      self.cleanup()
      return


  def showColorBox(self):
    self.colorNode = EditUtil.getColorNode()

    if not self.colorBox:
      self.colorBox = ColorBox.ColorBox(parameterNode=self.parameterNode, parameter=self.parameter, colorNode=self.colorNode)

    self.colorBox.show(parameterNode=self.parameterNode, parameter=self.parameter, colorNode=self.colorNode)

  def hideTerminology(self, flag):
    self.terminologyCollapsibleButton.collapsed = flag
