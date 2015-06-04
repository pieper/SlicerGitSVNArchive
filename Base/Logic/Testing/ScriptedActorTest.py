
layoutManager = slicer.app.layoutManager()
threeDView = layoutManager.threeDWidget(0).threeDView()
rw = threeDView.renderWindow()
rens = rw.GetRenderers()
renderer = rens.GetItemAsObject(0)

dummyMapper = vtk.vtkPolyDataMapper()
scriptedActor = slicer.vtkOpenGLScriptedActor()
scriptedActor.SetMapper(dummyMapper) # not really used, but needed so actor is called
scriptedActor.SetScript('Render()')
renderer.AddActor(scriptedActor)

def Render():
  glDisable( GL_CULL_FACE )
  ## Moves the drawing origin 1.5 units to the left
  glTranslatef(-1.5,0.0,0.0)
  ## Starts the geometry generation mode
  glBegin(GL_TRIANGLES)
  glVertex3f( 0.0,  1.0, 0.0)
  glVertex3f(-1.0, -1.0, 0.0)
  glVertex3f( 1.0, -1.0, 0.0)
  glEnd()

