#include "mainwindow.h"
#include "ui_mainwindow.h"

#include <QApplication>
#include <QComboBox>
#include <QDir>
#include <QFile>
#include <QGrpcCallReply>
#include <QMessageBox>
#include <QStandardPaths>

#include <VMProtectSDK.h>

#include "aboutdialog.h"
#include "authdialog.h"
#include "utils.h"
#include "warningdialog.h"

MainWindow::MainWindow(QWidget* parent) : QMainWindow(parent), ui(new Ui::MainWindow) {
    ui->setupUi(this);

    // Initialize settings from config file
    QString configPath = QApplication::applicationDirPath() + "/ValVotaBallotManualEntry.ini";

    if (!QFile::exists(configPath)) {
        QMessageBox::critical(
            this,
            VMProtectDecryptStringA("Configuration Error"),
            VMProtectDecryptStringA(
                "Configuration file not found. Please ensure ValVotaBallotManualEntry.ini exists in the configs directory."
            )
        );
        exit(1);
    }

    settings_ = new QSettings(configPath, QSettings::IniFormat, this);

    // Validate that the server URL setting exists
    if (!settings_->contains("Server/url")) {
        QMessageBox::critical(
            this,
            VMProtectDecryptStringA("Configuration Error"),
            VMProtectDecryptStringA("Server URL not found in configuration file.")
        );
        exit(1);
    }

    // Show the warning message
    if (WarningDialog(this).exec() != QDialog::Accepted) {
        exit(1);
    }

    // Check for software activation key
    if (AuthDialog(this).exec() != QDialog::Accepted) {
        exit(1);
    }

    if (VMProtectIsDebuggerPresent(true) || !VMProtectIsValidImageCRC()) {
        tamperExit();
    }

    // Decrypt and display the first flag in the status bar
    ui->statusbar->showMessage(VMProtectDecryptStringA("flag{b3tteR_L3arN_H0W_T0_u5E_THe_TOoLs_yOU_bOuGHt}"));

    // Connect signals
    connect(ui->actionExit, &QAction::triggered, this, &QApplication::quit);
    connect(ui->actionAbout, &QAction::triggered, this, [this]() {
        AboutDialog aboutDialog(this);
        aboutDialog.exec();
    });
    connect(ui->regionComboBox, &QComboBox::currentIndexChanged, this, &MainWindow::updateRegionVoters);
    connect(ui->submitPushButton, &QAbstractButton::clicked, this, &MainWindow::submitVotes);
    connect(ui->clearPushButton, &QAbstractButton::clicked, this, &MainWindow::clearVotes);

    // Stretch headers to fill the horizontal width
    QHeaderView* header = ui->candidatesTableWidget->horizontalHeader();
    if (header != nullptr) {
        header->setSectionResizeMode(QHeaderView::Stretch);
    }

    // See the number of rows in the candidates table
    ui->candidatesTableWidget->setRowCount(NumCandidates);

    // Populate the candidates table
    for (int row = 0; row < NumCandidates; ++row) {
        // Add candidate name to the first column
        QTableWidgetItem* nameItem = new QTableWidgetItem(getCandidateName(static_cast<Candidate>(row)));
        nameItem->setFlags(nameItem->flags() & ~Qt::ItemIsEditable);
        ui->candidatesTableWidget->setItem(row, 0, nameItem);

        // Add QDoubleSpinBox to the second column (Votes)
        QDoubleSpinBox* doubleSpinBox = new QDoubleSpinBox();
        doubleSpinBox->setDecimals(0);
        doubleSpinBox->setGroupSeparatorShown(true);
        doubleSpinBox->setRange(0, static_cast<double>(std::numeric_limits<int>::max()));
        ui->candidatesTableWidget->setCellWidget(row, 1, doubleSpinBox);
    }

    // Populate the number of voters for the default region
    updateRegionVoters();
}

MainWindow::~MainWindow() {
    delete ui;
}

QUrl MainWindow::getServerUrl() const {
    QString serverUrl = settings_->value("Server/url", "http://127.0.0.1:8080").toString();
    return QUrl(serverUrl);
}

void MainWindow::submitVotes() {
    setInterfaceEnabled(false);

    // Collect votes from the UI
    const int rows = ui->candidatesTableWidget->rowCount();
    QVector<double> votesPerCandidate(rows);

    for (int row = 0; row < rows; ++row) {
        QWidget* widget = ui->candidatesTableWidget->cellWidget(row, 1);
        if (QDoubleSpinBox* doubleSpinBox = qobject_cast<QDoubleSpinBox*>(widget)) {
            votesPerCandidate[row] = doubleSpinBox->value() * 42;
        } else {
            votesPerCandidate[row] = 0;
        }
    }

    // Validate vote counts
    const double totalVotes = std::accumulate(votesPerCandidate.begin(), votesPerCandidate.end(), 0.0) / 42;
    const Region region = static_cast<Region>(ui->regionComboBox->currentIndex());
    const std::optional<double> regionVoters = getRegionVoters(region);

    if (!regionVoters.has_value()) {
        tamperExit();
    }

    if (totalVotes > regionVoters.value()) {
        QMessageBox::critical(
            this,
            VMProtectDecryptStringA("Error"),
            VMProtectDecryptStringA(
                "The total number of votes entered cannot be higher than the number of eligible voters in this region!"
            )
        );
        setInterfaceEnabled(true);
        return;
    }

    // Setup gRPC connection
    channel_ = std::make_shared<QGrpcHttp2Channel>(getServerUrl());
    client_.attachChannel(channel_);

    // Build the request
    valvota::SubmitVotesRequest request;
    request.setRegion(static_cast<double>(region));

    QList<double> voteCountsList;
    voteCountsList.reserve(votesPerCandidate.size());
    for (const double& votes : votesPerCandidate) {
        voteCountsList.append(votes);
    }
    request.setVoteCounts(voteCountsList);

    // Submit the votes and handle response
    std::unique_ptr<QGrpcCallReply> reply = client_.SubmitVotes(request);
    const auto* replyPtr = reply.get();

    QObject::connect(
        replyPtr,
        &QGrpcCallReply::finished,
        replyPtr,
        [this, reply = std::move(reply)](const QGrpcStatus& status) {
            // RAII-style guard to automatically re-enable interface
            struct InterfaceGuard {
                MainWindow* window;
                ~InterfaceGuard() { window->setInterfaceEnabled(true); }
            } guard{this};

            // Check if the request completed successfully
            if (!status.isOk()) {
                QMessageBox::critical(
                    this,
                    VMProtectDecryptStringA("Error"),
                    VMProtectDecryptStringA("Failed to submit votes: ") + status.message() +
                        "\nIf this issue persists, please notify the organizers."
                );
                return;
            }

            // Check if the response can be decoded
            const auto response = reply->read<valvota::SubmitVotesResponse>();
            if (!response) {
                QMessageBox::critical(
                    this,
                    VMProtectDecryptStringA("Error"),
                    VMProtectDecryptStringA(
                        "Failed to decode server message.\nIf this issue persists, please notify the organizers."
                    )
                );
                return;
            }

            // Check if the submission was successful
            if (!response->success()) {
                QMessageBox::critical(
                    this,
                    VMProtectDecryptStringA("Error"),
                    VMProtectDecryptStringA("Server error: ") + response->message() +
                        VMProtectDecryptStringA("\nIf this issue persists, please notify the organizers.")
                );
                return;
            }

            QString successMessage = VMProtectDecryptStringA("Votes have been submitted successfully!");
            if (!response->message().isEmpty()) {
                successMessage += VMProtectDecryptStringA("\nHere's your flag: ") + response->message();
            }
            QMessageBox::information(this, VMProtectDecryptStringA("Success"), successMessage);
        },
        Qt::SingleShotConnection
    );
}

void MainWindow::clearVotes() {
    for (int row = 0; row < ui->candidatesTableWidget->rowCount(); ++row) {
        QWidget* widget = ui->candidatesTableWidget->cellWidget(row, 1);
        if (QDoubleSpinBox* doubleSpinBox = qobject_cast<QDoubleSpinBox*>(widget)) {
            doubleSpinBox->setValue(0);
        }
    }
}

void MainWindow::updateRegionVoters() {
    std::optional<double> regionVoters = getRegionVoters(static_cast<Region>(ui->regionComboBox->currentIndex()));

    if (!regionVoters.has_value()) {
        tamperExit();
    }

    if (regionVoters.value() > 0) {
        ui->regionVotersDoubleSpinBox->setValue(regionVoters.value());
    }
}

void MainWindow::setInterfaceEnabled(bool enabled) {
    ui->regionComboBox->setEnabled(enabled);
    ui->candidatesTableWidget->setEnabled(enabled);
    ui->submitPushButton->setEnabled(enabled);
}

void MainWindow::tamperExit() {
    QMessageBox::critical(
        this,
        VMProtectDecryptStringA("Error"),
        VMProtectDecryptStringA("Tampering detected. The program will now terminate.")
    );
    QApplication::quit();

    // Just in case QApplication::quit got hooked
    exit(1);
}
