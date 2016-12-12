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

// Qt includes
#include <QDebug>
#include <QNetworkCookieJar>
#include <QNetworkReply>
#include <QTime>
#include <QUrl>
#include <QWebEngineSettings>

// QtCore includes
#include <qSlicerPersistentCookieJar.h>

// QtGUI includes
#include "qSlicerWebWidget.h"
#include "ui_qSlicerWebWidget.h"

//-----------------------------------------------------------------------------
class qSlicerWebWidgetPrivate: public Ui_qSlicerWebWidget
{
  Q_DECLARE_PUBLIC(qSlicerWebWidget);
protected:
  qSlicerWebWidget* const q_ptr;

public:
  qSlicerWebWidgetPrivate(qSlicerWebWidget& object);

  void init();

  /// Convenient method to set "document.webkitHidden" property
  void setDocumentWebkitHidden(bool value);

  QTime DownloadTime;
};

// --------------------------------------------------------------------------
qSlicerWebWidgetPrivate::qSlicerWebWidgetPrivate(qSlicerWebWidget& object)
  :q_ptr(&object)
{
}

// --------------------------------------------------------------------------
void qSlicerWebWidgetPrivate::init()
{
  Q_Q(qSlicerWebWidget);

  this->setupUi(q);
  this->WebEngineView->installEventFilter(q);

  //this->WebEngineView->page()->setCookieJar(new qSlicerPersistentCookieJar());

  QObject::connect(this->WebEngineView, SIGNAL(loadStarted()),
                   q, SLOT(onLoadStarted()));

  QObject::connect(this->WebEngineView, SIGNAL(loadFinished(bool)),
                   q, SLOT(onLoadFinished(bool)));

  QObject::connect(this->WebEngineView, SIGNAL(loadProgress(int)),
                   this->ProgressBar, SLOT(setValue(int)));

  //QObject::connect(this, SIGNAL(javaScriptWindowObjectCleared()),
                   //q, SLOT(initJavascript()));

  //this->WebEngineView->settings()->setAttribute(QWebEngineSettings::DeveloperExtrasEnabled, true);

  this->ProgressBar->setVisible(false);

  //this->setScrollBarPolicy(Qt::Vertical, Qt::ScrollBarAlwaysOn);

  QObject::connect(this->WebEngineView->page(), SIGNAL(linkClicked(QUrl)),
                   q, SLOT(onLinkClicked(QUrl)));

#ifdef Slicer_USE_PYTHONQT_WITH_OPENSSL
  QObject::connect(this->WebEngineView->page(),
                   SIGNAL(sslErrors(QNetworkReply*, const QList<QSslError> & )),
                   q, SLOT(handleSslErrors(QNetworkReply*, const QList<QSslError> & )));
#endif
}

// --------------------------------------------------------------------------
void qSlicerWebWidgetPrivate::setDocumentWebkitHidden(bool value)
{
  Q_Q(qSlicerWebWidget);
  q->evalJS(QString("document.webkitHidden = %1").arg(value ? "true" : "false"));
}

// --------------------------------------------------------------------------
qSlicerWebWidget::qSlicerWebWidget(QWidget* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerWebWidgetPrivate(*this))
{
  Q_D(qSlicerWebWidget);
  d->init();
}

// --------------------------------------------------------------------------
qSlicerWebWidget::~qSlicerWebWidget()
{
}

// --------------------------------------------------------------------------
QWebEngineView * qSlicerWebWidget::webEngineView()
{
  Q_D(qSlicerWebWidget);
  return d->WebEngineView;
}

//-----------------------------------------------------------------------------
QString qSlicerWebWidget::evalJS(const QString &js)
{
  Q_D(qSlicerWebWidget);
  //return d->evaluateJavaScript(js).toString();
  d->WebEngineView->page()->runJavaScript(js, [](const QVariant &result){ qDebug() << "Async javascript result " << result; });
  return QString("JavaScript now runs async");
}

// --------------------------------------------------------------------------
void qSlicerWebWidget::onDownloadStarted(QNetworkReply* reply)
{
  Q_D(qSlicerWebWidget);
  connect(reply, SIGNAL(downloadProgress(qint64,qint64)),
          SLOT(onDownloadProgress(qint64,qint64)));
  d->DownloadTime.start();
  d->ProgressBar->setVisible(true);
}

// --------------------------------------------------------------------------
void qSlicerWebWidget::onDownloadProgress(qint64 bytesReceived, qint64 bytesTotal)
{
  Q_D(qSlicerWebWidget);

  // Calculate the download speed
  double speed = bytesReceived * 1000.0 / d->DownloadTime.elapsed();
  QString unit;
  if (speed < 1024)
    {
    unit = "bytes/sec";
    }
  else if (speed < 1024*1024) {
    speed /= 1024;
    unit = "kB/s";
    }
  else
    {
    speed /= 1024*1024;
    unit = "MB/s";
    }

  d->ProgressBar->setFormat(QString("%p% (%1 %2)").arg(speed, 3, 'f', 1).arg(unit));
  d->ProgressBar->setMaximum(bytesTotal);
  d->ProgressBar->setValue(bytesReceived);
}

// --------------------------------------------------------------------------
void qSlicerWebWidget::onDownloadFinished(QNetworkReply* reply)
{
  Q_D(qSlicerWebWidget);
  Q_UNUSED(reply);
  d->ProgressBar->reset();
  d->ProgressBar->setVisible(false);
}

// --------------------------------------------------------------------------
void qSlicerWebWidget::initJavascript()
{
  Q_D(qSlicerWebWidget);
  d->setDocumentWebkitHidden(!d->WebEngineView->isVisible());
}

// --------------------------------------------------------------------------
void qSlicerWebWidget::onLoadStarted()
{
  Q_D(qSlicerWebWidget);
  d->ProgressBar->setFormat("%p%");
  d->ProgressBar->setVisible(true);
}

// --------------------------------------------------------------------------
void qSlicerWebWidget::onLoadFinished(bool ok)
{
  Q_UNUSED(ok);
  Q_D(qSlicerWebWidget);
  d->ProgressBar->reset();
  d->ProgressBar->setVisible(false);
}

// --------------------------------------------------------------------------
void qSlicerWebWidget::onLinkClicked(const QUrl& url)
{
  this->webEngineView()->setUrl(url);
}

// --------------------------------------------------------------------------
void qSlicerWebWidget::handleSslErrors(QNetworkReply* reply,
                                       const QList<QSslError> &errors)
{
#ifdef QT_NO_OPENSSL
  Q_UNUSED(reply)
  Q_UNUSED(errors)
#else
  foreach (QSslError e, errors)
    {
    qDebug() << "[SSL] [" << qPrintable(reply->url().host().trimmed()) << "]"
             << qPrintable(e.errorString());
    }
#endif
}

// --------------------------------------------------------------------------
bool qSlicerWebWidget::eventFilter(QObject* obj, QEvent* event)
{
  Q_D(qSlicerWebWidget);
  Q_ASSERT(d->WebEngineView == obj);
  if (d->WebEngineView == obj && !event->spontaneous() &&
      (event->type() == QEvent::Show || event->type() == QEvent::Hide))
    {
    d->setDocumentWebkitHidden(!d->WebEngineView->isVisible());
    this->evalJS("if (typeof $ != 'undefined') {"
                 "  $.event.trigger({type: 'webkitvisibilitychange'})"
                 "} else { console.info('JQuery not loaded - Failed to trigger webkitvisibilitychange') }");
    }
  return QObject::eventFilter(obj, event);
}
