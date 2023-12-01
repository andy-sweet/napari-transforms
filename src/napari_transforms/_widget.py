from typing import TYPE_CHECKING

from qtpy.QtWidgets import QWidget

if TYPE_CHECKING:
    from napari import Viewer


class TransformsWidget(QWidget):
    # your QWidget.__init__ can optionally request the napari viewer instance
    # use a type annotation of 'napari.viewer.Viewer' for any parameter
    def __init__(self, viewer: "Viewer"):
        super().__init__()
        self.viewer = viewer
