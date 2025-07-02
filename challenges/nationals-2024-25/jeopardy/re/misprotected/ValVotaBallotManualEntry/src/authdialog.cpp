#include "authdialog.h"
#include "ui_authdialog.h"

#include <QMessageBox>

#include <VMProtectSDK.h>

AuthDialog::AuthDialog(QWidget* parent) : QDialog(parent), ui(new Ui::AuthDialog) {
    ui->setupUi(this);

    // Connect UI component signals
    connect(ui->authorizePushButton, &QPushButton::clicked, this, &AuthDialog::checkAuthorization);
    connect(ui->closePushButton, &QPushButton::clicked, this, &AuthDialog::reject);

    // Display the hardware ID of this computer
    int bufSize = VMProtectGetCurrentHWID(NULL, 0);
    char* hwidBuf = new char[bufSize];
    VMProtectGetCurrentHWID(hwidBuf, bufSize);
    ui->hwidLineEdit->setText(QString(hwidBuf));
    delete[] hwidBuf;
}

AuthDialog::~AuthDialog() {
    delete ui;
}

void AuthDialog::checkAuthorization() {
    QString serial = ui->serialPlainTextEdit->toPlainText();
    int serialState = VMProtectSetSerialNumber(serial.toStdString().c_str());

#ifdef QT_DEBUG
    accept();
    return;
#endif

    if (serialState == SERIAL_STATE_SUCCESS) {
        accept();
        return;
    }

    QMessageBox::critical(this, "Error", "The authorization code you entered is invalid. Please try again.");
}
