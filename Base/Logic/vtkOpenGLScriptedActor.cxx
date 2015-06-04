
#include "vtkOpenGLScriptedActor.h"

// TODO: generalize for non-slicer wrapped VTK
#define Slicer_USE_PYTHONQT
#define Slicer_USE_PYTHON


// SlicerCore includes
#include "vtkSlicerConfigure.h"

// VTK includes
#include "vtkPython.h"
#include "vtkMapper.h"
#include "vtkMatrix4x4.h"
#include "vtkObjectFactory.h"
#include "vtkOpenGLRenderer.h"
#include "vtkProperty.h"
#include "vtkOpenGL.h"

// STD includes
#include <math.h>

//----------------------------------------------------------------------------
vtkStandardNewMacro(vtkOpenGLScriptedActor);

//----------------------------------------------------------------------------
vtkOpenGLScriptedActor::vtkOpenGLScriptedActor()
{
  this->Script = NULL;
}

//----------------------------------------------------------------------------
vtkOpenGLScriptedActor::~vtkOpenGLScriptedActor()
{
  this->SetScript(NULL);
}

//----------------------------------------------------------------------------
// Actual scripted actor render method.
//
// This is essenitally the core of vtkOpenGLScriptedActor, but with the call
// to the mapper replaced by the invocation of a script.  In this case
// the mapper is optional, since it's rendering code is replaced by the script.
// But it can still be useful to have the mapper available to
// access rendering parameters.
//
// Care must be taken in the render script not to re-enter the render pipeline
// (e.g. don't call Render on any render windows or update the GUI loop).
//
void vtkOpenGLScriptedActor::Render(vtkRenderer *ren, vtkMapper *vtkNotUsed(mapper))
{
  if (this->Script == NULL){
	  vtkErrorMacro("No python script specified for scripted actor.");
	  return;
  }

  double opacity;

  // get opacity
  opacity = this->GetProperty()->GetOpacity();
  if (opacity == 1.0)
    {
	  glDepthMask (GL_TRUE);
    }
  else
    {
    // add this check here for GL_SELECT mode
    // If we are not picking, then don't write to the zbuffer
    // because we probably haven't sorted the polygons. If we
    // are picking, then translucency doesn't matter - we want to
    // pick the thing closest to us.
    GLint param[1];
    glGetIntegerv(GL_RENDER_MODE, param);
    if(param[0] == GL_SELECT )
      {
      glDepthMask(GL_TRUE);
      }
    else
      {
      if(ren->GetLastRenderingUsedDepthPeeling())
        {
        glDepthMask(GL_TRUE); // transparency with depth peeling
        }
      else
        {
        glDepthMask (GL_FALSE); // transparency with alpha blending
        }
      }
    }

  // build transformation
  if (!this->IsIdentity)
    {
    double *mat = this->GetMatrix()->Element[0];
    double mat2[16];
    mat2[0] = mat[0];
    mat2[1] = mat[4];
    mat2[2] = mat[8];
    mat2[3] = mat[12];
    mat2[4] = mat[1];
    mat2[5] = mat[5];
    mat2[6] = mat[9];
    mat2[7] = mat[13];
    mat2[8] = mat[2];
    mat2[9] = mat[6];
    mat2[10] = mat[10];
    mat2[11] = mat[14];
    mat2[12] = mat[3];
    mat2[13] = mat[7];
    mat2[14] = mat[11];
    mat2[15] = mat[15];

    // insert model transformation
    glMatrixMode( GL_MODELVIEW );
    glPushMatrix();
    glMultMatrixd(mat2);
    }


  //
  // invoke the script here
  //
  if ( this->Script)
    {
#ifdef Slicer_USE_PYTHONQT // TODO: generalize this for any wrapped VTK
    PyObject *main_module = PyImport_AddModule("__main__");
    PyObject *global_dict = PyModule_GetDict(main_module);

    PyObject *pyResult = 0;
    pyResult = PyRun_String(this->Script,
                         Py_file_input, global_dict, global_dict);

	  //qSlicerCoreApplication *slicerApp =qSlicerCoreApplication::application();
	  //slicerApp->corePythonManager()->executeString(this->Script);
#else
    vtkErrorMacro("Only python is currently supported.");
#endif
    }

  // pop transformation matrix
  if (!this->IsIdentity)
    {
    glMatrixMode( GL_MODELVIEW );
    glPopMatrix();
    }

  if (opacity != 1.0)
    {
    glDepthMask (GL_TRUE);
    }
}

//----------------------------------------------------------------------------
void vtkOpenGLScriptedActor::PrintSelf(ostream& os, vtkIndent indent)
{
  if ( this->Script )
    {
    os << indent << "Script: " << this->Script << "\n";
    }
  else
    {
    os << indent << "Script: (none)\n";
    }
  this->Superclass::PrintSelf(os,indent);
}
