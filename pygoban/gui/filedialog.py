from PyQt5 import QtCore, QtWidgets


def filename_from_opendialog(parent):
    return QtWidgets.QFileDialog.getOpenFileName(
        parent,
        QtCore.QCoreApplication.translate("Dialog", "Open Sgf-file"),
        "",
        "All Files (*);;Sgf Files (*.sgf)",
    )[0]


def filename_from_savedialog(parent):
    return QtWidgets.QFileDialog.getSaveFileName(
        parent,
        QtCore.QCoreApplication.translate("Dialog", "Save Sgf-file"),
        "",
        "All Files (*);;Sgf Files (*.sgf)",
    )[0]
