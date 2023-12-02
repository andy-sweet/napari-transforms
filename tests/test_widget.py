from napari.components import ViewerModel
from napari_transforms._widget import TransformsWidget
from pytestqt.qtbot import QtBot


def test_transforms_widget(qtbot: QtBot):
    viewer = ViewerModel()
    widget = TransformsWidget(viewer)
    qtbot.addWidget(widget)
    assert widget is not None
