#include "warningdialog.h"
#include "ui_warningdialog.h"

WarningDialog::WarningDialog(QWidget* parent) : QDialog(parent), ui(new Ui::WarningDialog) {
    ui->setupUi(this);

    connect(ui->authCheckBox, &QCheckBox::checkStateChanged, this, [this]() {
        ui->confirmPushButton->setEnabled(ui->authCheckBox->isChecked());
    });

    connect(ui->confirmPushButton, &QPushButton::clicked, this, &QDialog::accept);
    connect(ui->closePushButton, &QPushButton::clicked, this, &QDialog::reject);
}

WarningDialog::~WarningDialog() {
    delete ui;
}
