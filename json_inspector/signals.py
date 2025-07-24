from PyQt6 import QtCore


class WorkerSignals(QtCore.QObject):
    loaded = QtCore.pyqtSignal(
        object,
        list,
        tuple,
    )


class SearchSignals(QtCore.QObject):
    finished = QtCore.pyqtSignal(list)
