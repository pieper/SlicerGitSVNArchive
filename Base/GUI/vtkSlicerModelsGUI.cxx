#include "vtkObject.h"
#include "vtkObjectFactory.h"
#include "vtkCommand.h"
#include "vtkKWWidget.h"
#include "vtkSlicerModelsGUI.h"
#include "vtkSlicerApplication.h"
#include "vtkSlicerStyle.h"
#include "vtkSlicerModuleLogic.h"
//#include "vtkSlicerModelsLogic.h"
#include "vtkKWFrameWithLabel.h"

//---------------------------------------------------------------------------
vtkStandardNewMacro (vtkSlicerModelsGUI );
vtkCxxRevisionMacro ( vtkSlicerModelsGUI, "$Revision: 1.0 $");


//---------------------------------------------------------------------------
vtkSlicerModelsGUI::vtkSlicerModelsGUI ( ) {

    //this->SetLogic ( NULL );
    this->LoadModelButton = NULL;
}


//---------------------------------------------------------------------------
vtkSlicerModelsGUI::~vtkSlicerModelsGUI ( ) {
    if (this->LoadModelButton ) {
        this->LoadModelButton->Delete ( );
        this->LoadModelButton = NULL;
    }

    //this->SetLogic ( NULL );
}


//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::RemoveGUIObservers ( ) {
    this->LoadModelButton->RemoveObservers ( vtkCommand::ModifiedEvent,  (vtkCommand *)this->GUICommand);    
}


//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::AddGUIObservers ( ) {

    this->LoadModelButton->AddObserver ( vtkCommand::ModifiedEvent,  (vtkCommand *)this->GUICommand );    
}


//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::AddLogicObserver ( vtkSlicerModuleLogic *logic, int event ) {
    // Fill in
}

//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::RemoveLogicObserver ( vtkSlicerModuleLogic *logic, int event ) {
    // Fill in
}


//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::AddLogicObservers ( ) {
    // Fill in
}

//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::RemoveLogicObservers ( ) {
    // Fill in
}


//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::AddMRMLObserver ( vtkMRMLNode *node, int event ) {
    // Fill in
}

//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::RemoveMRMLObserver ( vtkMRMLNode *node, int event ) {
    // Fill in
}

//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::AddMRMLObservers ( ) {
    // Fill in
}

//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::RemoveMRMLObservers ( ) {
    // Fill in
}


    /*
//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::SetLogic ( vtkSlicerModelsLogic *logic ) {

    // Don't bother if already set.
    if ( logic == this->Logic ) {
        return;
    }
    // Remove observers from application logic
    if ( this->Logic != NULL ) {
        this->RemoveLogicObservers ( );
    }
    // Set pointer and add observers if not null
    this->Logic = logic;
    if ( this->Logic != NULL ) {
        this->AddLogicObservers ( );
    }
}
     */




//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::ProcessGUIEvents ( vtkObject *caller,
                                                    unsigned long event,
                                                    void *callData ) 
{
    vtkKWLoadSaveButton *filebrowse = vtkKWLoadSaveButton::SafeDownCast(caller);
    if (filebrowse == this->LoadModelButton  && event == vtkCommand::ModifiedEvent )
        {
            // If a file has been selected for loading...
            if ( this->LoadModelButton->GetFileName ( ) ) {
                this->ApplicationLogic->Connect ( filebrowse->GetFileName ( ) );
            }
        }
}



//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::ProcessLogicEvents ( vtkObject *caller,
                                                    unsigned long event,
                                                    void *callData ) {

}

//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::ProcessMRMLEvents ( vtkObject *caller,
                                                    unsigned long event,
                                                    void *callData ) {

}


//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::Enter ( ) {
}

//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::Exit ( ) {
}




//---------------------------------------------------------------------------
void vtkSlicerModelsGUI::BuildGUI ( ) {

    vtkSlicerApplication *app = (vtkSlicerApplication *)this->GetApplication();
    vtkSlicerStyle *style = app->GetSlicerStyle();

    // ---
    // MODULE GUI FRAME 
    // configure a page for a model loading UI for now.
    // later, switch on the modulesButton in the SlicerControlGUI
    // ---
    // create a page
    this->UIPanel->AddPage ( "Models", "Models", NULL );
    
    // HELP FRAME
    vtkKWFrameWithLabel *modHelpFrame = vtkKWFrameWithLabel::New ( );
    modHelpFrame->SetParent ( this->UIPanel->GetPageWidget ( "Models" ) );
    modHelpFrame->Create ( );
    modHelpFrame->CollapseFrame ( );
    modHelpFrame->SetLabelText ("Help");
    app->Script ( "pack %s -side top -anchor nw -fill x -padx 2 -pady 2 -in %s",
                  modHelpFrame->GetWidgetName(), this->UIPanel->GetPageWidget("Models")->GetWidgetName());

    // ---
    // LOAD FRAME            
    vtkKWFrameWithLabel *modLoadFrame = vtkKWFrameWithLabel::New ( );
    modLoadFrame->SetParent ( this->UIPanel->GetPageWidget ( "Models" ) );
    modLoadFrame->Create ( );
    modLoadFrame->SetLabelText ("Load");
    modLoadFrame->ExpandFrame ( );

    // add a file browser 
    this->LoadModelButton = vtkKWLoadSaveButton::New ( );
    this->LoadModelButton->SetParent ( modLoadFrame->GetFrame() );
    this->LoadModelButton->Create ( );
    this->LoadModelButton->SetText ("Choose a file to load");
    this->LoadModelButton->GetLoadSaveDialog()->SetFileTypes(
                                                             "{ {MRML Document} {.mrml .xml} }");
    app->Script ( "pack %s -side top -anchor nw -fill x -padx 2 -pady 2 -in %s",
                  modLoadFrame->GetWidgetName(), this->UIPanel->GetPageWidget("Models")->GetWidgetName());
    app->Script("pack %s -side top -anchor w -padx 2 -pady 4", 
                this->LoadModelButton->GetWidgetName());

    // ---
    // DISPLAY FRAME            
    vtkKWFrameWithLabel *modDisplayFrame = vtkKWFrameWithLabel::New ( );
    modDisplayFrame->SetParent ( this->UIPanel->GetPageWidget ( "Models" ) );
    modDisplayFrame->Create ( );
    //modDisplayFrame->SetBackgroundColor ( style->GetGUIBgColor() );
    modDisplayFrame->SetLabelText ("Display");
    modDisplayFrame->SetDefaultLabelFontWeightToNormal( );
    modDisplayFrame->CollapseFrame ( );
    app->Script ( "pack %s -side top -anchor nw -fill x -padx 2 -pady 2 -in %s",
                  modDisplayFrame->GetWidgetName(), this->UIPanel->GetPageWidget("Models")->GetWidgetName());

    modLoadFrame->Delete ( );
    modHelpFrame->Delete ( );
    modDisplayFrame->Delete ( );
}





