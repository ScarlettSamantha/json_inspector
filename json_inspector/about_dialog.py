from PyQt6 import QtWidgets, QtCore
from vars import VERSION


class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About JSON Inspector")
        self.setMinimumSize(450, 200)

        layout = QtWidgets.QVBoxLayout(self)

        name_label = QtWidgets.QLabel("<h2>JSON Inspector</h2>", self)
        name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        author_label = QtWidgets.QLabel("by Scarlett Verheul &lt;scarlett.verheul@gmail.com&gt;", self)
        author_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(author_label)

        version_label = QtWidgets.QLabel(f"Version: {VERSION}", self)
        version_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        repo_label = QtWidgets.QLabel(
            '<a href="https://git.scarlettbytes.nl/scarlett/json-inspector">'
            "https://git.scarlettbytes.nl/scarlett/json-inspector</a>",
            self,
        )
        repo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        repo_label.setOpenExternalLinks(True)
        layout.addWidget(repo_label)

        license_label = QtWidgets.QLabel(
            f"Copyright © {str(QtCore.QDate.currentDate().year())} Scarlett Verheul.\nLicensed under GNU GPL v3",
            self,
        )
        license_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(license_label)

        layout.addStretch()

        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok, self)
        btn_box.accepted.connect(self.accept)  # type: ignore
        layout.addWidget(btn_box)
