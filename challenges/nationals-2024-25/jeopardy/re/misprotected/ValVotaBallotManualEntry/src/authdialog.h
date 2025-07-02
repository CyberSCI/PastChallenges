#ifndef AUTHDIALOG_H
#define AUTHDIALOG_H

#include <QDialog>

namespace Ui {
class AuthDialog;
}

class AuthDialog : public QDialog {
    Q_OBJECT

   public:
    explicit AuthDialog(QWidget* parent = nullptr);
    ~AuthDialog();

   private:
    Ui::AuthDialog* ui;

    void checkAuthorization();
};

#endif  // AUTHDIALOG_H
