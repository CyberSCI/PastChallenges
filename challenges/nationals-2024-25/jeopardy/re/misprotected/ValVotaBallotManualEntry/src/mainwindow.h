#ifndef MAINWINDOW_H
#define MAINWINDOW_H

// #include "valvota.qpb.h"
#include "valvota_client.grpc.qpb.h"

#include <QGrpcHttp2Channel>
#include <QMainWindow>
#include <QSettings>
#include <QUrl>

QT_BEGIN_NAMESPACE
namespace Ui {
class MainWindow;
}
QT_END_NAMESPACE

class MainWindow : public QMainWindow {
    Q_OBJECT

   public:
    MainWindow(QWidget* parent = nullptr);
    ~MainWindow();

   private slots:
    void submitVotes();
    void clearVotes();
    void updateRegionVoters();

   private:
    Ui::MainWindow* ui;

    std::shared_ptr<QGrpcHttp2Channel> channel_;
    valvota::SubmitVotesService::Client client_;
    QSettings* settings_;

    QUrl getServerUrl() const;
    void setInterfaceEnabled(bool enabled);
    void tamperExit();
};
#endif  // MAINWINDOW_H
