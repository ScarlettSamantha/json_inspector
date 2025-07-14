from PyQt6 import QtCore, QtWidgets


class WorkerSignals(QtCore.QObject):
    loaded = QtCore.pyqtSignal(
        QtWidgets.QTreeWidgetItem,
        list,
        tuple,
    )


class SearchSignals(QtCore.QObject):
    finished = QtCore.pyqtSignal(list)
