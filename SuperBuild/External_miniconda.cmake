
set(proj miniconda)
if(NOT ${CMAKE_PROJECT_NAME}_USE_SYSTEM_python)
  list(APPEND ${proj}_DEPENDENCIES CTKAPPLAUNCHER)
endif()

# Include dependent projects if any
ExternalProject_Include_Dependencies(${proj} PROJECT_VAR proj DEPENDS_VAR ${proj}_DEPENDENCIES)

if(${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})
  message(FATAL_ERROR "Enabling ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj} is not supported !")
endif()

if(NOT DEFINED PYTHON_INCLUDE_DIR
  OR NOT DEFINED PYTHON_LIBRARY
  OR NOT DEFINED PYTHON_EXECUTABLE)

  set(python_DIR ${CMAKE_BINARY_DIR}/${proj})
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

  if(UNIX)
    set(python_IMPORT_SUFFIX so)
    if(APPLE)
      set(python_IMPORT_SUFFIX dylib)
    endif()
    set(slicer_PYTHON_SHARED_LIBRARY_DIR ${python_DIR}/lib)
    set(PYTHON_INCLUDE_DIR ${python_DIR}/include/python2.7)
    set(PYTHON_LIBRARY ${python_DIR}/lib/libpython2.7.${python_IMPORT_SUFFIX})
    set(PYTHON_EXECUTABLE ${python_DIR}/bin/SlicerPython)
    set(slicer_PYTHON_REAL_EXECUTABLE ${python_DIR}/bin/python)
  elseif(WIN32)
    set(slicer_PYTHON_SHARED_LIBRARY_DIR ${python_DIR}/bin)
    set(PYTHON_INCLUDE_DIR ${python_DIR}/include)
    set(PYTHON_LIBRARY ${python_DIR}/libs/python27.lib)
    set(PYTHON_EXECUTABLE ${python_DIR}/bin/SlicerPython.exe)
    set(slicer_PYTHON_REAL_EXECUTABLE ${python_DIR}/bin/python.exe)
  else()
    message(FATAL_ERROR "Unknown system !")
  endif()

    if(NOT ${CMAKE_PROJECT_NAME}_USE_SYSTEM_python)

    # Configure python launcher
    configure_file(
      SuperBuild/python_customPython_configure.cmake.in
      ${CMAKE_CURRENT_BINARY_DIR}/python_customPython_configure.cmake
      @ONLY)
    set(python_customPython_configure_args)

    if(PYTHON_ENABLE_SSL)
      set(python_customPython_configure_args -DOPENSSL_EXPORT_LIBRARY_DIR:PATH=${OPENSSL_EXPORT_LIBRARY_DIR})
    endif()

    ExternalProject_Add_Step(${proj} python_customPython_configure
      COMMAND ${CMAKE_COMMAND} ${python_customPython_configure_args}
        -P ${CMAKE_CURRENT_BINARY_DIR}/python_customPython_configure.cmake
      DEPENDEES install
      )

  endif()

  if(CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_CFG_INTDIR ${SAVED_CMAKE_CFG_INTDIR}) # Restore CMAKE_CFG_INTDIR
  endif()

  #-----------------------------------------------------------------------------
  # Launcher setting specific to build tree

  set(_lib_subdir lib)
  if(WIN32)
    set(_lib_subdir bin)
  endif()

  # library paths
  set(${proj}_LIBRARY_PATHS_LAUNCHER_BUILD ${python_DIR}/${_lib_subdir})
  mark_as_superbuild(
    VARS ${proj}_LIBRARY_PATHS_LAUNCHER_BUILD
    LABELS "LIBRARY_PATHS_LAUNCHER_BUILD"
    )

  # paths
  set(${proj}_PATHS_LAUNCHER_BUILD ${python_DIR}/bin)
  mark_as_superbuild(
    VARS ${proj}_PATHS_LAUNCHER_BUILD
    LABELS "PATHS_LAUNCHER_BUILD"
    )

  # pythonpath
  set(_pythonhome ${CMAKE_BINARY_DIR}/python-install)
  set(pythonpath_subdir lib/python2.7)
  if(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    set(pythonpath_subdir Lib)
  endif()

  set(${proj}_PYTHONPATH_LAUNCHER_BUILD
    ${_pythonhome}/${pythonpath_subdir}
    ${_pythonhome}/${pythonpath_subdir}/lib-dynload
    ${_pythonhome}/${pythonpath_subdir}/site-packages
    )
  mark_as_superbuild(
    VARS ${proj}_PYTHONPATH_LAUNCHER_BUILD
    LABELS "PYTHONPATH_LAUNCHER_BUILD"
    )

  # environment variables
  set(${proj}_ENVVARS_LAUNCHER_BUILD "PYTHONHOME=${python_DIR}")
  mark_as_superbuild(
    VARS ${proj}_ENVVARS_LAUNCHER_BUILD
    LABELS "ENVVARS_LAUNCHER_BUILD"
    )

  #-----------------------------------------------------------------------------
  # Launcher setting specific to install tree

  # library paths
  if(UNIX)
    # On windows, python libraries are installed along with the executable
    set(${proj}_LIBRARY_PATHS_LAUNCHER_INSTALLED <APPLAUNCHER_DIR>/lib/Python/lib)
    mark_as_superbuild(
      VARS ${proj}_LIBRARY_PATHS_LAUNCHER_INSTALLED
      LABELS "LIBRARY_PATHS_LAUNCHER_INSTALLED"
      )
  endif()

  # pythonpath
  set(${proj}_PYTHONPATH_LAUNCHER_INSTALLED
    <APPLAUNCHER_DIR>/lib/Python/${pythonpath_subdir}
    <APPLAUNCHER_DIR>/lib/Python/${pythonpath_subdir}/lib-dynload
    <APPLAUNCHER_DIR>/lib/Python/${pythonpath_subdir}/site-packages
    )
  mark_as_superbuild(
    VARS ${proj}_PYTHONPATH_LAUNCHER_INSTALLED
    LABELS "PYTHONPATH_LAUNCHER_INSTALLED"
    )

  # environment variables
  set(${proj}_ENVVARS_LAUNCHER_INSTALLED "PYTHONHOME=<APPLAUNCHER_DIR>/lib/Python")
  mark_as_superbuild(
    VARS ${proj}_ENVVARS_LAUNCHER_INSTALLED
    LABELS "ENVVARS_LAUNCHER_INSTALLED"
    )

  #-----------------------------------------------------------------------------
  # numpy
  #ExternalProject_Add_Step(${proj} ${proj}-install-numpy
  #COMMAND ${python_DIR}/bin/conda install --yes --quiet numpy
  #DEPENDEES install
  #)

  # Test: install scipy... OK
  # ExternalProject_Add_Step(${proj} ${proj}-install-scipy
  #   COMMAND ${python_DIR}/bin/conda install --yes --quiet scipy
  #   DEPENDEES ${proj}-install-numpy
  #   )

  # scipy
  #ExternalProject_Add_Step(${proj} ${proj}-install-scikit-learn
  #  COMMAND ${python_DIR}/bin/conda install --yes --quiet scikit-learn
  #  DEPENDEES ${proj}-install-numpy
  #  )
  #-----------------------------------------------------------------------------

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

if(WIN32)
  set(PYTHON_DEBUG_LIBRARY ${PYTHON_LIBRARY})
  mark_as_superbuild(VARS PYTHON_DEBUG_LIBRARY LABELS "FIND_PACKAGE")
  ExternalProject_Message(${proj} "PYTHON_DEBUG_LIBRARY:${PYTHON_DEBUG_LIBRARY}")
endif()
