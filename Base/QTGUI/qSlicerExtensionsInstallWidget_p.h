/*==============================================================================

  Program: 3D Slicer

  Copyright (c) Kitware Inc.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
  and was partially funded by NIH grant 3P41RR013218-12S1

==============================================================================*/

#ifndef __qSlicerExtensionsInstallWidgetPrivate_p_h
#define __qSlicerExtensionsInstallWidgetPrivate_p_h

// Qt includes
#include <QObject>
#include <QUrl>
#if (QT_VERSION < QT_VERSION_CHECK(5, 6, 0))
class QWebChannel;
#else
#include <QWebChannel>
#endif

// Slicer includes
class qSlicerExtensionsInstallWidget;
class qSlicerExtensionsManagerModel;
#include "qSlicerWebWidget_p.h"

// --------------------------------------------------------------------------
class ExtensionInstallWidgetWebChannelProxy : public QObject
{
  Q_OBJECT
public:
  ExtensionInstallWidgetWebChannelProxy():InstallWidget(0){}
  qSlicerExtensionsInstallWidget* InstallWidget;
public slots:
  void refresh();
private:
  Q_DISABLE_COPY(ExtensionInstallWidgetWebChannelProxy);
};

//-----------------------------------------------------------------------------
class qSlicerExtensionsInstallWidgetPrivate : public qSlicerWebWidgetPrivate
{
  Q_DECLARE_PUBLIC(qSlicerExtensionsInstallWidget);
protected:
  qSlicerExtensionsInstallWidget* const q_ptr;

public:
  qSlicerExtensionsInstallWidgetPrivate(qSlicerExtensionsInstallWidget& object);
  virtual ~qSlicerExtensionsInstallWidgetPrivate();

  /// Return the URL allowing to retrieve the extension list page
  /// associated with the current architecture, operating system and slicer revision.
  QUrl extensionsListUrl();

  void setFailurePage(const QStringList &errors);

  virtual void updateWebChannelScript(QByteArray& webChannelScript);
  virtual void initializeWebChannel(QWebChannel* webChannel);
  void registerExtensionsManagerModel(qSlicerExtensionsManagerModel* oldModel, qSlicerExtensionsManagerModel* newModel);

  qSlicerExtensionsManagerModel * ExtensionsManagerModel;

  QString SlicerRevision;
  QString SlicerOs;
  QString SlicerArch;

  bool BrowsingEnabled;
  bool NavigationRequestAccepted;

  ExtensionInstallWidgetWebChannelProxy* InstallWidgetForWebChannel;
};

#endif
