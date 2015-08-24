
set(proj miniconda)

# Include dependent projects if any
ExternalProject_Include_Dependencies(${proj} PROJECT_VAR proj DEPENDS_VAR ${proj}_DEPENDENCIES)

if(${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})
  message(FATAL_ERROR "Enabling ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj} is not supported !")
endif()

if(NOT DEFINED PYTHON_INCLUDE_DIR
  OR NOT DEFINED PYTHON_LIBRARY
  OR NOT DEFINED PYTHON_EXECUTABLE)

  set (python_DIR ${CMAKE_BINARY_DIR}/python-conda)
  file(MAKE_DIRECTORY ${python_DIR})

  # Choose install file depending on the platform version
  # TODO: host this file in a controlled repository
  if(UNIX)
    if(APPLE)
      set(PYTHON-INSTALL-FILE "https://www.dropbox.com/s/j68c3b9rhmvgqwv/Miniconda-Mac.tar.gz")
    else()
      set(PYTHON-INSTALL-FILE "https://www.dropbox.com/s/1xcwejg40u6b5mu/Miniconda-linux.tar.gz")
    endif()
    set(INSTALL_COMMAND bash ${python_DIR}-install/Miniconda-install.sh -f -b -p ${python_DIR})
  else()
    # Windows
    set(PYTHON-INSTALL-FILE "https://www.dropbox.com/s/34n1771as727pj0/Miniconda-Windows.tar.gz")
    set(INSTALL_COMMAND ${python_DIR}-install/Miniconda-3.8.3-Windows-x86_64.exe /InstallationType=AllUsers /S /D=${python_DIR})
  endif()

  ExternalProject_Add(${proj}
    URL ${PYTHON-INSTALL-FILE}
    #URL_MD5 "d3ad8868836e177ee4f9bd8bbd0c827a"
    DOWNLOAD_DIR ${python_DIR}-install
    SOURCE_DIR ${python_DIR}-install
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ""
    INSTALL_COMMAND ${INSTALL_COMMAND}
    )

  if(APPLE)
    ExternalProject_Add_Step(${proj} fix_rpath
      COMMAND install_name_tool -id ${python_DIR}/lib/libpython2.7.dylib ${python_DIR}/lib/libpython2.7.dylib
      DEPENDEES install
      )

    # hack: rename libsqlite3.dylib in order that CTK is building. Apparently is not needed, but it is referenced
    # from /System/Library/Frameworks/CoreData.framework/Versions/A/CoreData, neccesary to build CTK
    ExternalProject_Add_Step(${proj} rename_libsqlite
      COMMAND mv ${python_DIR}/lib/libsqlite3.dylib ${python_DIR}/lib/libsqlite3.dylib.bak
      DEPENDEES install
    )
  endif()

  # Test: install numpy (requires to disable Slicer Numpy).... OK
  ExternalProject_Add_Step(${proj} installNumpy
    COMMAND ${python_DIR}/bin/conda install --yes --quiet numpy
    DEPENDEES install
    )

  # Test: install scipy... OK
  # ExternalProject_Add_Step(${proj} installSciPy
  #   COMMAND ${python_DIR}/bin/conda install --yes --quiet scipy
  #   DEPENDEES installNumpy
  #   )

  ExternalProject_Add_Step(${proj} installSciPy
    COMMAND ${python_DIR}/bin/conda install --yes --quiet scikit-learn
    DEPENDEES installNumpy
    )

else()
  ExternalProject_Add_Empty(${proj} DEPENDS ${${proj}_DEPENDENCIES})
endif()

mark_as_superbuild(
  VARS
    PYTHON_EXECUTABLE:FILEPATH
    PYTHON_INCLUDE_DIR:PATH
    PYTHON_LIBRARY:FILEPATH
  LABELS "FIND_PACKAGE"
  )

ExternalProject_Message(${proj} "PYTHON_EXECUTABLE:${PYTHON_EXECUTABLE}")
ExternalProject_Message(${proj} "PYTHON_INCLUDE_DIR:${PYTHON_INCLUDE_DIR}")
ExternalProject_Message(${proj} "PYTHON_LIBRARY:${PYTHON_LIBRARY}")