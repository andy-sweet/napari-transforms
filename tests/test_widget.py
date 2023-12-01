import numpy as np
from napari_transforms._widget import TransformsWidget


def test_transforms_widget(make_napari_viewer):
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100)))

    my_widget = TransformsWidget(viewer)

    assert my_widget is not None
