
import unittest
import slicer
import EditorLib

class EditorLibTesting(unittest.TestCase):
  def setUp(self):
    pass

  def test_ThresholdThreading(self):
    """
    Replicate the issue reported in bug 1822 where spliting
    a grow-cut produced volume causes a multi-threading related
    issue on mac release builds
    """

    #
    # first, get some sample data
    #
    import SampleData
    sampleDataLogic = SampleData.SampleDataLogic()
    head = sampleDataLogic.downloadMRHead()

    #
    # create a label map and set it for editing
    #
    volumesLogic = slicer.modules.volumes.logic()
    # AF: intentionally use the naming convention that does not match the one
    # used by Editor
    headLabel = volumesLogic.CreateLabelVolume( slicer.mrmlScene, head, head.GetName() + '-segmentation' )
    
    selectionNode = slicer.app.applicationLogic().GetSelectionNode()
    selectionNode.SetReferenceActiveVolumeID( head.GetID() )
    selectionNode.SetReferenceActiveLabelVolumeID( headLabel.GetID() )
    slicer.app.applicationLogic().PropagateVolumeSelection(0)

    #
    # Instantiate a new widget, and add Editor widget to it
    #
    from Editor import EditorWidget
    editorWidget = EditorWidget(showVolumesFrame=False)
