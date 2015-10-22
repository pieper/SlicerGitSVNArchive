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

    # Category row:
    self.terminologyCategoryFrame = qt.QFrame(self.terminologyCollapsibleButton)
    self.terminologyCategoryFrame.setLayout(qt.QHBoxLayout())
    self.terminologyCollapsibleButton.layout().addWidget(self.terminologyCategoryFrame)

    # Category
    self.terminologyCategoryLabel = qt.QLabel(self.terminologyCategoryFrame)
    self.terminologyCategoryLabel.setText("Category: ")
    self.terminologyCategoryFrame.layout().addWidget(self.terminologyCategoryLabel)

    self.terminologyCategoryLineEdit = qt.QLineEdit(self.terminologyCategoryFrame)
    self.terminologyCategoryLineEdit.setText("")
    # for now, read only
    self.terminologyCategoryLineEdit.setReadOnly(1);
    self.terminologyCategoryFrame.layout().addWidget(self.terminologyCategoryLineEdit )

    # Category type:
    self.terminologyCategoryTypeLabel = qt.QLabel(self.terminologyCategoryFrame)
    self.terminologyCategoryTypeLabel.setText("Type: ")
    self.terminologyCategoryFrame.layout().addWidget(self.terminologyCategoryTypeLabel)

    self.terminologyCategoryTypeLineEdit = qt.QLineEdit(self.terminologyCategoryFrame)
    self.terminologyCategoryTypeLineEdit.setText("")
    # for now, read only
    self.terminologyCategoryTypeLineEdit.setReadOnly(1);
    self.terminologyCategoryFrame.layout().addWidget(self.terminologyCategoryTypeLineEdit )

    # Category modifier:
    self.terminologyCategoryModifierLabel = qt.QLabel(self.terminologyCategoryFrame)
    self.terminologyCategoryModifierLabel.setText("Modifier: ")
    self.terminologyCategoryFrame.layout().addWidget(self.terminologyCategoryModifierLabel)

    self.terminologyCategoryModifierLineEdit = qt.QLineEdit(self.terminologyCategoryFrame)
    self.terminologyCategoryModifierLineEdit.setText("")
    # for now, read only
    self.terminologyCategoryModifierLineEdit.setReadOnly(1);
    self.terminologyCategoryFrame.layout().addWidget(self.terminologyCategoryModifierLineEdit )

    # Region row
    self.terminologyRegionFrame = qt.QFrame(self.terminologyCollapsibleButton)
    self.terminologyRegionFrame.setLayout(qt.QHBoxLayout())
    self.terminologyCollapsibleButton.layout().addWidget(self.terminologyRegionFrame)

    # Region:
    self.terminologyRegionLabel = qt.QLabel(self.terminologyRegionFrame)
    self.terminologyRegionLabel.setText("Region: ")
    self.terminologyRegionFrame.layout().addWidget(self.terminologyRegionLabel)

    self.terminologyRegionLineEdit = qt.QLineEdit(self.terminologyRegionFrame)
    self.terminologyRegionLineEdit.setText("")
    # for now, read only
    self.terminologyRegionLineEdit.setReadOnly(1);
    self.terminologyRegionFrame.layout().addWidget(self.terminologyRegionLineEdit )

    # Region type:
    self.terminologyRegionTypeLabel = qt.QLabel(self.terminologyRegionFrame)
    self.terminologyRegionTypeLabel.setText("Type: ")
    self.terminologyRegionFrame.layout().addWidget(self.terminologyRegionTypeLabel)

    self.terminologyRegionTypeLineEdit = qt.QLineEdit(self.terminologyRegionFrame)
    self.terminologyRegionTypeLineEdit.setText("")
    # for now, read only
    self.terminologyRegionTypeLineEdit.setReadOnly(1);
    self.terminologyRegionFrame.layout().addWidget(self.terminologyRegionTypeLineEdit )

    # Region modifier:
    self.terminologyRegionModifierLabel = qt.QLabel(self.terminologyRegionFrame)
    self.terminologyRegionModifierLabel.setText("Modifier: ")
    self.terminologyRegionFrame.layout().addWidget(self.terminologyRegionModifierLabel)

    self.terminologyRegionModifierLineEdit = qt.QLineEdit(self.terminologyRegionFrame)
    self.terminologyRegionModifierLineEdit.setText("")
    # for now, read only
    self.terminologyRegionModifierLineEdit.setReadOnly(1);
    self.terminologyRegionFrame.layout().addWidget(self.terminologyRegionModifierLineEdit )

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
          print 'Have a terminology: ', terminologyName
          colorLogic = slicer.modules.colors.logic()
          if colorLogic:
            # enable the terminology widgets
            self.hideTerminology(0)
            category = colorLogic.GetCategoryFromLabel(label, terminologyName)
            categoryType = colorLogic.GetCategoryTypeFromLabel(label, terminologyName)
            categoryModifier = colorLogic.GetCategoryModifierFromLabel(label, terminologyName)
            self.terminologyCategoryLineEdit.setText(category)
            self.terminologyCategoryTypeLineEdit.setText(categoryType)
            self.terminologyCategoryModifierLineEdit.setText(categoryModifier)
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
