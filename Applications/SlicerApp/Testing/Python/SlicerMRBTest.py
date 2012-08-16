
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
    for tractName in tracts:
      self.showOneTract(tracts,tractName)
      self.storeSceneView('%s-view' % tractName, "Only show tubes for %s" % tractName)

    #
    # save the mrml scene to a temp directory, then zip it
    #
    sceneSaveDirectory = self.tempDirectory('__scene__')
    mrbSaveFilePath= self.tempDirectory('__mrb__') + '/test.mrb'
    print("Saving scene to: %s" % sceneSaveDirectory)
    print("Saving mrb to: %s" % mrbSaveFilePath)
    self.saveSceneToDirectory(sceneSaveDirectory)
    self.zipToMRB(sceneSaveDirectory, mrbSaveFilePath)


  def showOneTract(self,tracts,whichTract): 
    """display the named tract's tubes but turn the others off"""
    for tractName in tracts:
      fiberNode = slicer.util.getNode(tractName)
      tubeDisplay = fiberNode.GetTubeDisplayNode()
      if tractName == whichTract:
        tubeDisplay.SetVisibility(1)
        tubeDisplay.SetSliceIntersectionVisibility(1) 
      else:
        tubeDisplay.SetVisibility(0)
        tubeDisplay.SetSliceIntersectionVisibility(0) 

  def storeSceneView(self,name,description=""):
    """  Store a scene view into the current scene.
    TODO: this might move to slicer.util
    """
    layoutManager = slicer.app.layoutManager()
    
    sceneViewNode = slicer.vtkMRMLSceneViewNode()
    view1 = layoutManager.threeDWidget(0).threeDView()
    
    w2i1 = vtk.vtkWindowToImageFilter()
    w2i1.SetInput(view1.renderWindow())
    
    w2i1.Update()
    image1 = w2i1.GetOutput()
    sceneViewNode.SetScreenShot(image1)
    sceneViewNode.UpdateSnapshotScene(slicer.mrmlScene)
    slicer.mrmlScene.AddNode(sceneViewNode)

    sceneViewNode.SetName(name)
    sceneViewNode.SetSceneViewDescription(description)
    sceneViewNode.StoreScene()

    return sceneViewNode

  def tempDirectory(self,key='__SlicerTestTemp__'):
    """Come up with a unique directory name in the temp dir and make it and return it
    # TODO: switch to QTemporaryDir in Qt5.
    # For now, create a named directory
    """
    tempDir = qt.QDir(slicer.app.temporaryPath)
    tempDirName = key + qt.QDateTime().currentDateTime().toString("yyyy-MM-dd_hh+mm+ss.zzz")
    packFileInfo = qt.QFileInfo(qt.QDir(tempDir), tempDirName)
    dirPath = packFileInfo.absoluteFilePath()
    qt.QDir().mkpath(dirPath)
    return dirPath

  def saveSceneToDirectory(self,directoryPath):
    """Save the current mrml scene to the given directory"""

    applicationLogic = slicer.app.applicationLogic()
    applicationLogic.SaveSceneToSlicerDataBundleDirectory(directoryPath, None)

  def zipToMRB(self,directoryPath,mrbPath):
    """Convert the scene directory to an mrb file"""
    applicationLogic = slicer.app.applicationLogic()
    applicationLogic.Zip(mrbPath,directoryPath)

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


