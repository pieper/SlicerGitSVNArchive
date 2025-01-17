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
#include <QVBoxLayout>
#if (QT_VERSION < QT_VERSION_CHECK(5, 6, 0))
#include <QWebFrame>
#include <QWebView>
#else
#include <QCoreApplication>
#include <QWebEngineView>
#include <QWebChannel>
#include <QWebEngineScript>
#include <QWebEnginePage>
#include <QWebEngineProfile>
#include <QWebEngineScriptCollection>
#include <QFile>
#endif

// QtCore includes
#include <qSlicerPersistentCookieJar.h>

// QtGUI includes
#include "qSlicerWebWidget.h"
#include "qSlicerWebWidget_p.h"

// --------------------------------------------------------------------------
#if (QT_VERSION >= QT_VERSION_CHECK(5, 6, 0))
namespace
{
class qSlicerWebEngineView : public QWebEngineView
{
public:
  qSlicerWebEngineView(QWidget *parent = Q_NULLPTR) : QWebEngineView(parent){}
  virtual ~qSlicerWebEngineView(){}
  virtual QSize sizeHint() const
  {
    // arbitrary values to address https://issues.slicer.org/view.php?id=4613
    return QSize(150, 150);
  }
};
}

// --------------------------------------------------------------------------
qSlicerWebEnginePage::qSlicerWebEnginePage(QWebEngineProfile *profile, QObject *parent)
  : QWebEnginePage(profile, parent),
    WebWidget(nullptr)
{
}

// --------------------------------------------------------------------------
qSlicerWebEnginePage::~qSlicerWebEnginePage()
{
}
#endif

// --------------------------------------------------------------------------
qSlicerWebWidgetPrivate::qSlicerWebWidgetPrivate(qSlicerWebWidget& object)
  :q_ptr(&object)
{
}

// --------------------------------------------------------------------------
qSlicerWebWidgetPrivate::~qSlicerWebWidgetPrivate()
{
}

// --------------------------------------------------------------------------
void qSlicerWebWidgetPrivate::init()
{
  Q_Q(qSlicerWebWidget);

  this->setupUi(q);
#if (QT_VERSION < QT_VERSION_CHECK(5, 6, 0))
  this->WebView = new QWebView();
#else
  this->WebView = new qSlicerWebEngineView();

  QWebEngineProfile *profile = new QWebEngineProfile("MyWebChannelProfile", q);

  QFile webChannelJsFile(":/qtwebchannel/qwebchannel.js");

  if (!webChannelJsFile.open(QIODevice::ReadOnly))
    {
    qWarning() << QString("Couldn't open qwebchannel.js file: %1").arg(webChannelJsFile.errorString());
    }
  else
    {
    QByteArray webChannelJs = webChannelJsFile.readAll();
    this->updateWebChannelScript(webChannelJs);
    QWebEngineScript script;
    script.setSourceCode(webChannelJs);
    script.setName("qwebchannel_appended.js");
    script.setWorldId(QWebEngineScript::MainWorld);
    script.setInjectionPoint(QWebEngineScript::DocumentCreation);
    script.setRunsOnSubFrames(false);
    profile->scripts()->insert(script);
    }

  this->WebEnginePage = new qSlicerWebEnginePage(profile, this->WebView);
  this->WebEnginePage->WebWidget = q;
  this->WebView->setPage(this->WebEnginePage);
  this->WebChannel = new QWebChannel(this->WebView->page());
  this->initializeWebChannel(this->WebChannel);
  this->WebView->page()->setWebChannel(this->WebChannel);

  // XXX Since relying on automatic deletion of QWebEngineView when the application
  // exit causes the application to crash. This is a workaround for explicitly
  // deleting the object before the application exit.
  // See https://bugreports.qt.io/browse/QTBUG-50160#comment-305211
  QObject::connect(QCoreApplication::instance(), SIGNAL(aboutToQuit()),
                   this, SLOT(onAppAboutToQuit()));
#endif
  this->verticalLayout->insertWidget(0, this->WebView);

  this->WebView->installEventFilter(q);

  QObject::connect(this->WebView, SIGNAL(loadStarted()),
                   q, SLOT(onLoadStarted()));

  QObject::connect(this->WebView, SIGNAL(loadFinished(bool)),
                   q, SLOT(onLoadFinished(bool)));

  QObject::connect(this->WebView, SIGNAL(loadProgress(int)),
                   this->ProgressBar, SLOT(setValue(int)));

  this->ProgressBar->setVisible(false);

#if (QT_VERSION < QT_VERSION_CHECK(5, 6, 0))
  QNetworkAccessManager * networkAccessManager = this->WebView->page()->networkAccessManager();
  Q_ASSERT(networkAccessManager);
  networkAccessManager->setCookieJar(new qSlicerPersistentCookieJar());

  QObject::connect(this->mainFrame(), SIGNAL(javaScriptWindowObjectCleared()),
                   q, SLOT(initJavascript()));

  this->WebView->settings()->setAttribute(QWebSettings::DeveloperExtrasEnabled, true);

  this->mainFrame()->setScrollBarPolicy(Qt::Vertical, Qt::ScrollBarAlwaysOn);

  QObject::connect(this->WebView->page(), SIGNAL(linkClicked(QUrl)),
                   q, SLOT(onLinkClicked(QUrl)));
#endif

#ifdef Slicer_USE_PYTHONQT_WITH_OPENSSL
#if (QT_VERSION < QT_VERSION_CHECK(5, 6, 0))
  QObject::connect(networkAccessManager,
                   SIGNAL(sslErrors(QNetworkReply*, const QList<QSslError> & )),
                   q, SLOT(handleSslErrors(QNetworkReply*, const QList<QSslError> & )));
#else
  // See qSlicerWebEnginePage::certificateError
#endif
#endif
}

// --------------------------------------------------------------------------
#if (QT_VERSION < QT_VERSION_CHECK(5, 6, 0))
QWebFrame* qSlicerWebWidgetPrivate::mainFrame()
{
  return this->WebView->page()->mainFrame();
}
#endif

// --------------------------------------------------------------------------
void qSlicerWebWidgetPrivate::onAppAboutToQuit()
{
#if (QT_VERSION >= QT_VERSION_CHECK(5, 6, 0))
  if (this->WebView)
    {
    this->WebView->setParent(0);
    delete this->WebView;
    this->WebView = 0;
    }
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

//-----------------------------------------------------------------------------
qSlicerWebWidget::qSlicerWebWidget(
  qSlicerWebWidgetPrivate* pimpl, QWidget* _parent)
  : Superclass(_parent), d_ptr(pimpl)
{
  // Note: You are responsible to call init() in the constructor of derived class.
}

// --------------------------------------------------------------------------
qSlicerWebWidget::~qSlicerWebWidget()
{
}

// --------------------------------------------------------------------------
#if (QT_VERSION < QT_VERSION_CHECK(5, 6, 0))
QWebView *
#else
QWebEngineView *
#endif
qSlicerWebWidget::webView()
{
  Q_D(qSlicerWebWidget);
  return d->WebView;
}

//-----------------------------------------------------------------------------
QString qSlicerWebWidget::evalJS(const QString &js)
{
  Q_D(qSlicerWebWidget);

#if (QT_VERSION < QT_VERSION_CHECK(5, 6, 0))
  return d->mainFrame()->evaluateJavaScript(js).toString();
#else
  // NOTE: Beginning Qt5.7, the call to runJavaScript becomes asynchronous,
  // and generally it takes a function lambda which is called once
  // the script evaluation is completed. This takes in the result string
  // as an argument.
  // Since the result of JavaScript evaluation is not used anywhere
  // in the code base, the function lambda is not supplied here,
  // and an empty string is returned instead.
  // When the need arises to use the result string, function lambdas
  // and resulting infrastructure will have to be provided.
  d->WebView->page()->runJavaScript(js);
  return QString();
#endif

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
  d->setDocumentWebkitHidden(!d->WebView->isVisible());
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
#if (QT_VERSION < QT_VERSION_CHECK(5, 6, 0))
void qSlicerWebWidget::onLinkClicked(const QUrl& url)
{
  this->webView()->setUrl(url);
}
#else
bool qSlicerWebWidget::acceptNavigationRequest(const QUrl & url, QWebEnginePage::NavigationType type, bool isMainFrame)
{
  Q_D(qSlicerWebWidget);
  Q_ASSERT(d->WebEnginePage);
  return d->WebEnginePage->webEnginePageAcceptNavigationRequest(url, type, isMainFrame);
}
#endif

// --------------------------------------------------------------------------
void qSlicerWebWidget::handleSslErrors(QNetworkReply* reply,
                                       const QList<QSslError> &errors)
{
#if (QT_VERSION < QT_VERSION_CHECK(5, 3, 0))
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
#else
#ifdef QT_NO_SSL
  Q_UNUSED(reply)
  Q_UNUSED(errors)
#else
  foreach (QSslError e, errors)
    {
    qDebug() << "[SSL] [" << qPrintable(reply->url().host().trimmed()) << "]"
             << qPrintable(e.errorString());
    }
#endif
#endif
}

// --------------------------------------------------------------------------
bool qSlicerWebWidget::eventFilter(QObject* obj, QEvent* event)
{
  Q_D(qSlicerWebWidget);
  Q_ASSERT(d->WebView == obj);
  if (d->WebView == obj && !event->spontaneous() &&
      (event->type() == QEvent::Show || event->type() == QEvent::Hide))
    {
    d->setDocumentWebkitHidden(!d->WebView->isVisible());
    this->evalJS("if (typeof $ != 'undefined') {"
                 "  $.event.trigger({type: 'webkitvisibilitychange'})"
                 "} else { console.info('JQuery not loaded - Failed to trigger webkitvisibilitychange') }");
    }
  return QObject::eventFilter(obj, event);
}
