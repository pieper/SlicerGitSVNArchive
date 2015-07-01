import os
import string
from __main__ import vtk, qt, ctk, slicer
import numpy
import dicom
from DICOMLib import DICOMPlugin
from DICOMLib import DICOMLoadable

#
# This is the plugin to handle translation of DICOM objects
# that can be represented as multivolume objects
# from DICOM files into MRML nodes.  It follows the DICOM module's
# plugin architecture.
#

class DICOMUltrasoundPluginClass(DICOMPlugin):
  """ Ultrasound specific interpretation code
  """

  def __init__(self):
    super(DICOMUltrasoundPluginClass,self).__init__()
    self.loadType = "Ultrasound"

    self.tags['sopClassUID'] = "0008,0016"

  def examine(self,fileLists):
    """ Returns a list of DICOMLoadable instances
    corresponding to ways of interpreting the
    fileLists parameter.
    """
    loadables = []
    allfiles = []
    for files in fileLists:
      loadables += self.examineFiles(files)
      allfiles += files

    return loadables

  def examineFiles(self,files):
    """ Returns a list of DICOMLoadable instances
    corresponding to ways of interpreting the
    files parameter.
    """
    loadables = []

    if len(files) > 1:
      # there should only be one instance per 4D volume
      return []

    filePath = files[0]
    sopClassUID = slicer.dicomDatabase.fileValue(filePath,self.tags['sopClassUID'])

    if sopClassUID != '1.2.840.113543.6.6.1.3.10002':
      # currently only this one (bogus, non-standard) format is supported
      return []

    loadable = DICOMLoadable()
    loadable.files = files
    loadable.name = "Philips 4D Ultrasound"
    loadable.tooltip = loadable.name
    loadable.selected = True
    loadable.confidence = 1.
    loadables.append(loadable)

    ds = dicom.read_file(filePath, stop_before_pixels=True)

    if ds.PhotometricInterpretation != 'MONOCHROME2':
      logging.warning('Warning: unsupported PhotometricInterpretation')
      loadable.confidence = .4

    if ds.BitsAllocated != 8 or ds.BitsStored != 8 or ds.HighBit != 7:
      logging.warning('Warning: Bad scalar type (not unsigned byte)')
      loadable.confidence = .4

    if ds.PhysicalUnitsXDirection != 3 or ds.PhysicalUnitsYDirection != 3:
      logging.warning('Warning: Units not in centimeters')
      loadable.confidence = .4

    if ds.SamplesPerPixel != 1:
      logging.warning('Warning: multiple samples per pixel')
      loadable.confidence = .4

    return loadables

  def load(self,loadable):
    """Load the selection as an Ultrasound, store in MultiVolume
    """

    # get the key info from the "fake" dicom file
    filePath = loadable.files[0]
    ds = dicom.read_file(filePath, stop_before_pixels=True)
    columns = ds.Columns
    rows = ds.Rows
    slices = ds[(0x3001,0x1001)].value # private tag!
    spacing = (
            ds.PhysicalDeltaX * 10,
            ds.PhysicalDeltaY * 10,
            ds[(0x3001,0x1003)].value * 10 # private tag!
            )
    frames  = int(ds.NumberOfFrames)
    imageComponents = frames

    # create the correct size and shape vtkImageData
    image = vtk.vtkImageData()
    imageShape = (slices, rows, columns, frames)
    image.SetDimensions(columns, rows, slices)
    image.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, imageComponents)
    from vtk.util.numpy_support import vtk_to_numpy
    imageArray = vtk_to_numpy(image.GetPointData().GetScalars()).reshape(imageShape)

    # put the data in a numpy array
    # -- we need to read the file as raw bytes
    pixelShape = (frames, slices, rows, columns)
    pixels = numpy.fromfile(filePath, dtype=numpy.uint8)
    pixelSize = reduce(lambda x,y : x*y, pixelShape)
    headerSize = len(pixels)-pixelSize
    pixels = pixels[headerSize:]
    pixels = pixels.reshape(pixelShape)

    slicer.modules.imageArray = imageArray
    slicer.modules.pixels = pixels

    # copy the data from numpy to vtk (need to shuffle frames to components)
    for frame in range(frames):
      imageArray[:,:,:,frame] = pixels[frame]

    # create the multivolume node and display it
    multiVolumeNode = slicer.vtkMRMLMultiVolumeNode()

    multiVolumeNode.SetScene(slicer.mrmlScene)

    multiVolumeDisplayNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLMultiVolumeDisplayNode')
    multiVolumeDisplayNode.SetReferenceCount(multiVolumeDisplayNode.GetReferenceCount()-1)
    multiVolumeDisplayNode.SetScene(slicer.mrmlScene)
    multiVolumeDisplayNode.SetDefaultColorMap()
    slicer.mrmlScene.AddNode(multiVolumeDisplayNode)

    multiVolumeNode.SetAndObserveDisplayNodeID(multiVolumeDisplayNode.GetID())
    multiVolumeNode.SetAndObserveImageData(image)
    multiVolumeNode.SetNumberOfFrames(frames)
    multiVolumeNode.SetName(loadable.name)
    slicer.mrmlScene.AddNode(multiVolumeNode)

    #
    # automatically select the volume to display
    #
    appLogic = slicer.app.applicationLogic()
    selNode = appLogic.GetSelectionNode()
    selNode.SetReferenceActiveVolumeID(multiVolumeNode.GetID())
    appLogic.PropagateVolumeSelection()

    return multiVolumeNode



#
# DICOMUltrasoundPlugin
#

class DICOMUltrasoundPlugin:
  """
  This class is the 'hook' for slicer to detect and recognize the plugin
  as a loadable scripted module
  """
  def __init__(self, parent):
    parent.title = "DICOM Ultrasound Import Plugin"
    parent.categories = ["Developer Tools.DICOM Plugins"]
    parent.contributors = ["Steve Pieper, Isomics Inc."]
    parent.helpText = """
    Plugin to the DICOM Module to parse and load Ultrasound data from DICOM files.
    No module interface here, only in the DICOM module
    """
    parent.acknowledgementText = """
    This DICOM Plugin was developed by Steve Pieper, Isomics, Inc.
    based on MultiVolume example code by Andrey Fedorov, BWH.
    and was partially funded by NIH grants U01CA151261 and 3P41RR013218.
    """

    # don't show this module - it only appears in the DICOM module
    parent.hidden = True

    # Add this extension to the DICOM module's list for discovery when the module
    # is created.  Since this module may be discovered before DICOM itself,
    # create the list if it doesn't already exist.
    try:
      slicer.modules.dicomPlugins
    except AttributeError:
      slicer.modules.dicomPlugins = {}
    slicer.modules.dicomPlugins['DICOMUltrasoundPlugin'] = DICOMUltrasoundPluginClass


def patchPhilipsDICOM(dirPath):
  """
  Since CTK (rightly) requires certain basic information [1] before it can import
  data files that purport to be dicom, this code patches the files in a directory
  with some needed fields.  Apparently it is possible to export files from the
  Philips PMS QLAB system with these fields missing.

  Calling this function with a directory path will make a patched copy of each file.
  Importing the old files to CTK should still fail, but the new ones should work.

  The directory is assumed to have a set of instances that are all from the
  same study of the same patient.  Also that each instance (file) is an
  independent (multiframe) series.

  [1] https://github.com/commontk/CTK/blob/16aa09540dcb59c6eafde4d9a88dfee1f0948edc/Libs/DICOM/Core/ctkDICOMDatabase.cpp#L1283-L1287
  """

  tagsToSave = [
    'ImageType',
    'SOPClassUID',
    'SOPInstanceUID',
    'StudyDate',
    'ContentDate',
    'StudyTime',
    'ContentTime',
    'AccessionNumber',
    'Modality',
    'Manufacturer',
    'ReferringPhysiciansName',
    'PatientsName',
    'PatientID',
    'PatientsBirthDate',
    'PatientsSex',
    'FrameTime',
    'PhysicalUnitsXDirection',
    'PhysicalUnitsYDirection',
    'PhysicalDeltaX',
    'PhysicalDeltaY',
    'StudyInstanceUID',
    'SeriesInstanceUID',
    'StudyID',
    'SeriesNumber',
    'InstanceNumber',
    'ImageComments',
    'SamplesperPixel',
    'PhotometricInterpretation',
    'NumberofFrames',
    'Rows',
    'Columns',
    'BitsAllocated',
    'BitsStored',
    'HighBit',
    'PixelRepresentation',
    'PixelData']
  studyUIDToRandomUIDMap = {}
  seriesUIDToRandomUIDMap = {}
  patientIDToRandomIDMap = {}
  for root, subFolders, files in os.walk(dirPath):
    for file in files:
      filePath = os.path.join(root,file)
      print('Examining %s...' % file)

      try:
        ds = dicom.read_file(filePath)
      except IOError:
        print('Skipping non-dicom file')
        continue

      # first, remove any keys that are not known to be safe
      for key in ds.keys():
        tagName = dicom.datadict.get_entry(key)[3]
        if not tagName in tagsToSave:
          ds.__delattr__(tagName)

      # next get the random ids - re-use if we have
      # seen them before
      if ds.StudyInstanceUID not in studyUIDToRandomUIDMap:
        studyUIDToRandomUIDMap[ds.StudyInstanceUID] = dicom.UID.generate_uid(None)
      ds.StudyInstanceUID = studyUIDToRandomUIDMap[ds.StudyInstanceUID]
      if ds.SeriesInstanceUID not in studyUIDToRandomUIDMap:
        seriesUIDToRandomUIDMap[ds.SeriesInstanceUID] = dicom.UID.generate_uid(None)
      ds.SeriesInstanceUID = seriesUIDToRandomUIDMap[ds.SeriesInstanceUID]
      if ds.PatientID not in patientUIDToRandomUIDMap:
        patientUIDToRandomUIDMap[ds.PatientID] = dicom.UID.generate_uid(None)
      ds.PatientID = patientUIDToRandomUIDMap[ds.PatientID]


      # now explicitly set the values that we want to override
      ds.SOPInstanceUID = dicom.UID.generate_uid(None)
      if ds.PatientName == '':
        ds.PatientName = "Unspecified Patient"
      ds.StudyDate = "19000101"
      ds.ContentDate = "19000101"
      ds.StudyTime = "000000"
      ds.ContentTime = "000000"
      ds.AccessionNumber = "unknown"
      ds.ReferringPhysiciansName = "unknown"
      ds.PatientsBirthDate = "19000101"
      ds.PatientsSex = "O"
      ds.StudyID = "unknown"

      patchedFilePath = filePath + "-patched"
      dicom.write_file(patchedFilePath, ds)
      print('Writing patched %s...' % file)

