// Qt includes
#include <QApplication>

// SlicerQt includes
#include "qSlicerMouseModeToolBar.h"

// MRML includes
#include <vtkMRMLInteractionNode.h>
#include <vtkMRMLScene.h>
#include <vtkMRMLSelectionNode.h>

// Logic includes
#include <vtkSlicerApplicationLogic.h>

// STD includes

int qSlicerMouseModeToolBarTest1(int argc, char * argv[] )
{
  QApplication app(argc, argv);
  qSlicerMouseModeToolBar mouseToolBar;
  
  // set the scene without the app logic
  vtkMRMLScene* scene = vtkMRMLScene::New();
  mouseToolBar.setMRMLScene(scene);

  // now reset it to null and set with app logic
  vtkSlicerApplicationLogic *appLogic = vtkSlicerApplicationLogic::New();
  mouseToolBar.setMRMLScene(NULL);
  appLogic->SetMRMLScene(scene);
  mouseToolBar.setApplicationLogic(appLogic);
  mouseToolBar.setMRMLScene(scene);

  std::cout << "Done set up, starting testing..." << std::endl;

  // exercise public slots
  mouseToolBar.switchToViewTransformMode();
  mouseToolBar.switchPlaceMode();
  mouseToolBar.onPersistenceToggled();
  // without a qSlicerApplication, setting the cursor is a noop
  mouseToolBar.changeCursorTo(QCursor(Qt::BusyCursor));

  QString activeActionText;
  activeActionText = mouseToolBar.activeActionText();
  std::cout << "Active action text = " << qPrintable(activeActionText) << std::endl;

  /*
  // get the selection and interaction nodes that the mouse mode tool bar
  // listens to
  vtkMRMLNode *mrmlNode;
  vtkMRMLSelectionNode *selectionNode = NULL;
  //QString activeActionText;
  mrmlNode = scene->GetNodeByID("vtkMRMLSelectionNodeSingleton");
  if (mrmlNode)
    {
    selectionNode = vtkMRMLSelectionNode::SafeDownCast(mrmlNode);
    }
  if (selectionNode)
    {
    std::cout << "Got selection node" << std::endl;
    // add the new annotation types to it
    selectionNode->AddNewAnnotationIDToList("vtkMRMLAnnotationFiducialNode", ":/Icons/AnnotationPointWithArrow.png");
    selectionNode->AddNewAnnotationIDToList("vtkMRMLAnnotationRulerNode", ":/Icons/AnnotationDistanceWithArrow.png");
    selectionNode->SetReferenceActiveAnnotationID("vtkMRMLAnnotationFiducialNode");
    activeActionText = mouseToolBar.activeActionText();
    std::cout << "After setting selection node active annotation id to " << selectionNode->GetActiveAnnotationID() << ", mouse tool bar active action text = " << qPrintable(activeActionText) << std::endl;
    selectionNode->SetReferenceActiveAnnotationID("vtkMRMLAnnotationRulerNode");
    activeActionText = mouseToolBar.activeActionText();
    std::cout << "After setting selection node active annotation id to " << selectionNode->GetActiveAnnotationID() << ", mouse tool bar active action text = " << qPrintable(activeActionText) << std::endl;
    }
  
  vtkMRMLInteractionNode *interactionNode = NULL;
  mrmlNode = scene->GetNodeByID("vtkMRMLInteractionNodeSingleton");
  if (mrmlNode)
    {
    interactionNode = vtkMRMLInteractionNode::SafeDownCast(mrmlNode);
    }
  if (interactionNode)
    {
    std::cout << "Got interaction node" << std::endl;
    interactionNode->SetPlaceModePersistence(1);
    interactionNode->SetPlaceModePersistence(0);
    interactionNode->SwitchToSinglePlaceMode();
    if (selectionNode)
      {
      selectionNode->SetReferenceActiveAnnotationID("vtkMRMLAnnotationFiducialNode");
      activeActionText = mouseToolBar.activeActionText();
      std::cout << "After setting selection node active annotation id to " << selectionNode->GetActiveAnnotationID() << ", mouse tool bar active action text = " << qPrintable(activeActionText) << std::endl;
      }
    interactionNode->SwitchToViewTransformMode();
    activeActionText = mouseToolBar.activeActionText();
    std::cout << "After switching interaction node to view transform, active action text = " << qPrintable(activeActionText) << std::endl;
    }
  */

  // clean up
  appLogic->Delete();
  scene->Delete();


  return EXIT_SUCCESS;
}

