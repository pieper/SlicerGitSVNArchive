/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer
  Module:    $RCSfile: vtkMRMLColorLogic.h,v $
  Date:      $Date$
  Version:   $Revision$

=========================================================================auto=*/

#ifndef __vtkMRMLColorLogic_h
#define __vtkMRMLColorLogic_h

// MRMLLogic includes
#include "vtkMRMLAbstractLogic.h"
#include "vtkMRMLLogicWin32Header.h"

// MRML includes
class vtkMRMLColorNode;
class vtkMRMLColorTableNode;
class vtkMRMLFreeSurferProceduralColorNode;
class vtkMRMLProceduralColorNode;
class vtkMRMLPETProceduralColorNode;
class vtkMRMLdGEMRICProceduralColorNode;
class vtkMRMLColorTableNode;

// STD includes
#include <cstdlib>
#include <vector>

/// \brief MRML logic class for color manipulation.
///
/// This class manages the logic associated with reading, saving,
/// and changing propertied of the colors.
class VTK_MRML_LOGIC_EXPORT vtkMRMLColorLogic : public vtkMRMLAbstractLogic
{
public:
  struct StandardTerm
    {
    std::string CodeValue;
    std::string CodeMeaning;
    std::string CodingSchemeDesignator;

    StandardTerm(){
      CodeValue = "";
      CodeMeaning = "";
      CodingSchemeDesignator = "";
    }

    void PrintSelf(ostream &os){
      os << "Code value: " << CodeValue << " Code meaning: " << CodeMeaning << " Code scheme designator: " << CodingSchemeDesignator << std::endl;
    }
    };

  struct ColorLabelCategorization
    {
    unsigned LabelValue;
    StandardTerm SegmentedPropertyCategory;
    StandardTerm SegmentedPropertyType;
    StandardTerm SegmentedPropertyTypeModifier;

    void PrintSelf(ostream &os){
      os << "Label: " << LabelValue << std::endl <<
        "   Segmented property category: ";
      SegmentedPropertyCategory.PrintSelf(os);
        os << "   Segmented property type: ";
      SegmentedPropertyType.PrintSelf(os);
        os << "   Segmented property type modifier: ";
      SegmentedPropertyTypeModifier.PrintSelf(os);
      os << std::endl;
    };
    };


  /// The Usual vtk class functions
  static vtkMRMLColorLogic *New();
  vtkTypeMacro(vtkMRMLColorLogic,vtkMRMLAbstractLogic);
  void PrintSelf(ostream& os, vtkIndent indent);

  /// Add a series of color nodes, setting the types to the defaults, so that
  /// they're accessible to the rest of Slicer
  /// Each node is a singleton and is not included in a saved scene. The color
  /// node singleton tags are the same as the node IDs:
  /// vtkMRMLColorTableNodeGrey, vtkMRMLPETProceduralColorNodeHeat, etc.
  virtual void AddDefaultColorNodes();

  /// Remove the colour nodes that were added
  virtual void RemoveDefaultColorNodes();

  /// Return the default color table node id for a given type
  static const char * GetColorTableNodeID(int type);

  /// Return the default freesurfer color node id for a given type
  static const char * GetFreeSurferColorNodeID(int type);

  /// Return the default dGEMRIC color node id for a given type
  static const char * GetdGEMRICColorNodeID(int type);

  /// Return the default PET color node id for a given type
  static const char * GetPETColorNodeID(int type);

  /// return a default color node id for a procedural color node
  /// Delete the returned char* to avoid memory leak
  static const char * GetProceduralColorNodeID(const char *name);

  /// return a default color node id for a file based node, based on the file name
  /// Delete the returned char* to avoid memory leak
  static const char * GetFileColorNodeID(const char *fileName);
  static std::string  GetFileColorNodeSingletonTag(const char * fileName);

  /// Return a default color node id for a freesurfer label map volume
  virtual const char * GetDefaultFreeSurferLabelMapColorNodeID();

  /// Return a default color node id for a volume
  virtual const char * GetDefaultVolumeColorNodeID();

  /// Return a default color node id for a label map
  virtual const char * GetDefaultLabelMapColorNodeID();

  /// Return a default color node id for the editor
  virtual const char * GetDefaultEditorColorNodeID();

  /// Return a default color node id for a model
  virtual const char * GetDefaultModelColorNodeID();

  /// Return a default color node id for a chart
  virtual const char * GetDefaultChartColorNodeID();

  /// Add a file to the input list Files, checking first for null, duplicates
  void AddColorFile(const char *fileName, std::vector<std::string> *Files);

  /// Load in a color file, creating a storage node. Returns a pointer to the
  /// created node on success, 0 on failure (no file, invalid color file). The
  /// name of the created color node is \a nodeName if specified or
  /// the fileName otherwise. Try first to load it as a color table
  /// node, then if that fails, as a procedural color node. It calls
  /// CreateFileNode or CreateProceduralFileNode which are also used
  /// for the built in color nodes, so it has to unset some flags: set
  /// the category to File, turn save with scene on on the node and
  /// it's storage node, turn off hide from editors, remove the
  /// singleton tag.
  /// \sa CreateFileNode, CreateProceduralFileNode
  vtkMRMLColorNode* LoadColorFile(const char *fileName, const char *nodeName = NULL);

  /// Get/Set the user defined paths where to look for extra colour files
  vtkGetStringMacro(UserColorFilePaths);
  vtkSetStringMacro(UserColorFilePaths);

  /// Returns a vtkMRMLColorTableNode copy (type = vtkMRMLColorTableNode::User)
  /// of the \a color node. The node is not added to the scene and you are
  /// responsible for deleting it.
  static vtkMRMLColorTableNode* CopyNode(vtkMRMLColorNode* colorNode, const char* copyName);

  /// Returns a vtkMRMLProceduralColorNode copy (type = vtkMRMLColorTableNode::User)
  /// of the \a color node. The node is not added to the scene and you are
  /// responsible for deleting it. If there is no color transfer function on the
  /// input node, for example if it's a color table node, it will return a
  /// procedural node with a blank color transfer function.
  static vtkMRMLProceduralColorNode* CopyProceduralNode(vtkMRMLColorNode* colorNode, const char* copyName);

  bool LookupCategorizationFromLabel(int label, ColorLabelCategorization&, const char *lutName = NULL);
  bool LookupLabelFromCategorization(ColorLabelCategorization&, int&, const char *lutName = NULL);
  bool PrintCategorizationFromLabel(int label, const char *lutName = NULL);

  /// utility methods to look up the terminology
  /// If the lutName is null, defaults to GenericAnatomyColors
  std::string GetCategoryFromLabel(int label, const char *lutName = NULL);
  std::string GetCategoryTypeFromLabel(int label, const char *lutName = NULL);
  std::string GetCategoryModifierFromLabel(int label, const char *lutName = NULL);

protected:
  vtkMRMLColorLogic();
  virtual ~vtkMRMLColorLogic();
  // disable copy constructor and operator
  vtkMRMLColorLogic(const vtkMRMLColorLogic&);
  void operator=(const vtkMRMLColorLogic&);

  /// Reimplemented to listen to specific scene events
  virtual void SetMRMLSceneInternal(vtkMRMLScene* newScene);

  /// Called when the scene fires vtkMRMLScene::NewSceneEvent.
  /// We add the default LUTs.
  virtual void OnMRMLSceneNewEvent();

  vtkMRMLColorTableNode* CreateLabelsNode();
  vtkMRMLColorTableNode* CreateDefaultTableNode(int type);
  vtkMRMLProceduralColorNode* CreateRandomNode();
  vtkMRMLProceduralColorNode* CreateRedGreenBlueNode();
  vtkMRMLFreeSurferProceduralColorNode* CreateFreeSurferNode(int type);
  vtkMRMLColorTableNode* CreateFreeSurferFileNode(const char* fileName);
  vtkMRMLPETProceduralColorNode* CreatePETColorNode(int type);
  vtkMRMLdGEMRICProceduralColorNode* CreatedGEMRICColorNode(int type);
  vtkMRMLColorTableNode* CreateDefaultFileNode(const std::string& colorname);
  vtkMRMLColorTableNode* CreateUserFileNode(const std::string& colorname);
  vtkMRMLColorTableNode* CreateFileNode(const char* fileName);
  vtkMRMLProceduralColorNode* CreateProceduralFileNode(const char* fileName);

  void AddLabelsNode();
  void AddDefaultTableNode(int i);
  void AddDefaultProceduralNodes();
  void AddFreeSurferNode(int type);
  void AddFreeSurferFileNode(vtkMRMLFreeSurferProceduralColorNode* basicFSNode);
  void AddPETNode(int type);
  void AddDGEMRICNode(int type);
  void AddDefaultFileNode(int i);
  void AddUserFileNode(int i);

  void AddDefaultTableNodes();
  void AddFreeSurferNodes();
  void AddPETNodes();
  void AddDGEMRICNodes();
  void AddDefaultFileNodes();
  void AddUserFileNodes();

  virtual std::vector<std::string> FindDefaultColorFiles();
  virtual std::vector<std::string> FindUserColorFiles();
  virtual std::vector<std::string> FindDefaultTerminologyColorFiles();

  void AddDefaultTerminologyColors();
  bool InitializeTerminologyMappingFromFile(std::string mapFile);

  /// Return the ID of a node that doesn't belong to a scene.
  /// It is the concatenation of the node class name and its type.
  static const char * GetColorNodeID(vtkMRMLColorNode* colorNode);

  /// a vector holding discovered default colour files, found in the
  /// Resources/ColorFiles directory, white space separated with:
  /// int name r g b a
  /// with rgba in the range 0-255
  std::vector<std::string> ColorFiles;

  /// a vector holding discovered default terminology files that are
  /// linked with default Slicer color files (not all color files
  /// have terminology files). Found in the Terminology subdirectory
  /// of the ColorFiles directory, they are comma separated value files
  /// with:
  /// Integer Label,Text Label,Segmented Property Category -- CID 7150++,Segmented Property Type,Segmented Property Type Modifier,Color
  /// Integer Label is a number
  /// Text Label is the name of the color
  /// Segmented Property * is as defined by the terminology standard, inside brackets
  /// Color is rgb(r;g;b) where each of r, g, b are in teh range 0-255
  /// The first non commented line in the file gives the name of the Slicer LUT,
  /// for example:
  /// SlicerLUT=GenericAnatomyColors
  std::vector<std::string> TerminologyColorFiles;

  /// a vector holding discovered user defined colour files, found in the
  /// UserColorFilesPath directories.
  std::vector<std::string> UserColorFiles;
  /// a string holding delimiter separated (; on win32, : else) paths where to
  /// look for extra colour files, set from the return value of
  /// vtkMRMLApplication::GetColorFilePaths
  char *UserColorFilePaths;

  // mappings used for terminology color look ups
  typedef std::map<int,ColorLabelCategorization> ColorCategorizationMapType;
  std::map<std::string, ColorCategorizationMapType> colorCategorizationMaps;

  static std::string TempColorNodeID;

 private:

  std::string RemoveLeadAndTrailSpaces(std::string);
  bool ParseTerm(std::string, StandardTerm&);

};

#endif
