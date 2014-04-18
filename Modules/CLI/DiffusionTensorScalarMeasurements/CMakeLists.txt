
#-----------------------------------------------------------------------------
set(MODULE_NAME DiffusionTensorScalarMeasurements)

#-----------------------------------------------------------------------------
SEMMacroBuildCLI(
  NAME ${MODULE_NAME}
  LOGO_HEADER ${Slicer_SOURCE_DIR}/Resources/ITKLogo.h
  TARGET_LIBRARIES MRMLCore vtkTeem
  INCLUDE_DIRECTORIES
    ${vtkTeem_INCLUDE_DIRS}
    ${MRMLCore_INCLUDE_DIRS}
  EXECUTABLE_ONLY
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)
  add_subdirectory(Testing)
endif()
