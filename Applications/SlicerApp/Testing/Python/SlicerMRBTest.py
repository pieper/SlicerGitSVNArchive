
import os
import unittest
import slicer
import EditorLib

class SlicerMRB(unittest.TestCase):
  """ Test for slicer data bundle

Run manually from within slicer:
execfile('/Users/pieper/slicer4/latest/Slicer/Applications/SlicerApp/Testing/Python/SlicerMRBTest.py'); t = SlicerMRB(); t.setUp(); t.runTest()
  """
  def setUp(self):
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    self.test_SlicerMRB()

  def test_SlicerMRB(self):
    """
    Replicate the issue reported in bug 2385 where saving
    and restoring an MRB file does not work.
    """

    #
    # first, get the data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5766', 'DTIVolume.raw.gz', None),
        ('http://slicer.kitware.com/midas3/download?items=5765', 'DTIVolume.nhdr', slicer.util.loadVolume),
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        ('http://slicer.kitware.com/midas3/download?items=5768', 'tract1.vtk', slicer.util.loadFiberBundle),
        ('http://slicer.kitware.com/midas3/download?items=5769', 'tract2.vtk', slicer.util.loadFiberBundle),
        ('http://slicer.kitware.com/midas3/download?items=5770', 'tract3.vtk', slicer.util.loadFiberBundle),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        print('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        print('Loading %s...\n' % (name,))
        loader(filePath)
    print('Finished with download and loading\n')

    #
    # set up the view of the tracts and scene views
    #
    tracts = ('tract1', 'tract2', 'tract3',)
    tractColors = ( (0.2, 0.9, 0.3), (0.9, 0.3, 0.3), (0.2, 0.4, 0.9) )
    for tractName,tubeColor in zip(tracts, tractColors):
      fiberNode = slicer.util.getNode(tractName)
      tubeDisplay = fiberNode.GetTubeDisplayNode()
      tubeDisplay.SetColor(tubeColor)
      tubeDisplay.SetColorModeToSolid()

    # turn on one at a time and save scene view
    for tractName tracts:
      for tractOffName tracts:
        fiberNode = slicer.util.getNode(tractOffName)
        tubeDisplay = fiberNode.GetTubeDisplayNode()
        tubeDisplay.SetVisibility(0)
        tubeDisplay.SetSliceIntersectionVisibility(0) 
      fiberNode = slicer.util.getNode(tractName)
      tubeDisplay = fiberNode.GetTubeDisplayNode()
      tubeDisplay.SetVisibility(1)
      tubeDisplay.SetSliceIntersectionVisibility(1) 




    #
    # set up the scene views
    #





#
# SlicerMRBTest
#

class SlicerMRBTest:
  """
  This class is the 'hook' for slicer to detect and recognize the test
  as a loadable scripted module (with a hidden interface)
  """
  def __init__(self, parent):
    parent.title = "SlicerMRBTest"
    parent.categories = ["Testing"]
    parent.contributors = ["Steve Pieper (Isomics Inc.)"]
    parent.helpText = """
    Self test for the editor.
    No module interface here, only used in SelfTests module
    """
    parent.acknowledgementText = """
    This DICOM Plugin was developed by
    Steve Pieper, Isomics, Inc.
    and was partially funded by NIH grant 3P41RR013218.
    """

    # don't show this module
    parent.hidden = True

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['SlicerMRBTest'] = self.runTest

  def runTest(self):
    tester = SlicerMRB()
    tester.setUp()
    tester.runTest()


#
# SlicerMRBTestWidget
#

class SlicerMRBTestWidget:
  def __init__(self, parent = None):
    self.parent = parent

  def setup(self):
    # don't display anything for this widget - it will be hidden anyway
    pass

  def enter(self):
    pass

  def exit(self):
    pass


