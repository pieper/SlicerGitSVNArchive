/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Author: Steve Pieper, Isomics, Inc.

=========================================================================auto=*/
// .NAME vtkOpenGLScriptedActor - OpenGL actor
// .SECTION Description
// vtkOpenGLScriptedActor is a concrete implementation of the abstract class vtkScriptedActor.
// vtkOpenGLScriptedActor interfaces to the OpenGL rendering library via a script.
// Currently only Python is supported (use PyOpenGL which must be installed).

#ifndef __vtkOpenGLScriptedActor_h
#define __vtkOpenGLScriptedActor_h

#include "vtkSlicerBaseLogic.h"

// VTK includes
#include "vtkActor.h"

class vtkOpenGLRenderer;

class VTK_SLICER_BASE_LOGIC_EXPORT vtkOpenGLScriptedActor : public vtkActor
{
protected:

public:
  static vtkOpenGLScriptedActor *New();
  vtkTypeMacro(vtkOpenGLScriptedActor,vtkActor);
  void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // Actual actor render method.
  void Render(vtkRenderer *ren, vtkMapper *mapper);

  // Description:
  // The string to execute to implement rendering of the actor
  // - user should embed references to appropriate Renderer, Actor and Mapper
  //   in the script so it can reference the data contained in them in order
  //   to implement the rendering
  vtkGetStringMacro(Script);
  vtkSetStringMacro(Script);

protected:
  vtkOpenGLScriptedActor();
  ~vtkOpenGLScriptedActor();

private:
  vtkOpenGLScriptedActor(const vtkOpenGLScriptedActor&);  // Not implemented.
  void operator=(const vtkOpenGLScriptedActor&);  // Not implemented.

  char *Script;
};

#endif

