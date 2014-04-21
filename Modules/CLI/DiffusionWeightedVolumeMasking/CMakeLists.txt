
#-----------------------------------------------------------------------------
set(MODULE_NAME DiffusionWeightedVolumeMasking)

find_package(VTK REQUIRED)
include(${VTK_USE_FILE})

if(${VTK_VERSION_MAJOR} GREATER 5)
  set(VTK_LIBRARIES
    vtkImagingMorphological
    )
endif()

#-----------------------------------------------------------------------------
SEMMacroBuildCLI(
  NAME ${MODULE_NAME}
  LOGO_HEADER ${Slicer_SOURCE_DIR}/Resources/ITKLogo.h
  TARGET_LIBRARIES MRMLCore vtkTeem vtkSlicerEditorLibModuleLogic ${VTK_LIBRARIES}
  INCLUDE_DIRECTORIES
    ${vtkITK_INCLUDE_DIRS}
    ${MRMLCore_INCLUDE_DIRS}
    ${vtkTeem_INCLUDE_DIRS}
    ${vtkSlicerEditorLibModuleLogic_SOURCE_DIR}
    ${vtkSlicerEditorLibModuleLogic_BINARY_DIR}
  EXECUTABLE_ONLY
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)
  add_subdirectory(Testing)
endif()
