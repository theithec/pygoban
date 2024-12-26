from PyQt5.QtCore import QCoreApplication  # pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QWidget, QFileDialog  # pylint: disable=no-name-in-module


def filename_from_opendialog(parent: QWidget):
    return QFileDialog.getOpenFileName(
        parent,
        QCoreApplication.translate("Dialog", "Open Sgf-file"),
        "",
        "All Files (*);;Sgf Files (*.sgf)",
    )[0]


def filename_from_savedialog(parent):
    return QFileDialog.getSaveFileName(
        parent,
        QCoreApplication.translate("Dialog", "Save Sgf-file"),
        "",
        "All Files (*);;Sgf Files (*.sgf)",
    )[0]
