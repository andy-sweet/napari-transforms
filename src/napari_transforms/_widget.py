from typing import TYPE_CHECKING, Optional, Tuple

import numpy as np
from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from superqt import QCollapsible

from napari_transforms._widget_utils import MatrixEdit, VectorEdit

if TYPE_CHECKING:
    from napari.components import ViewerModel
    from napari.layers import Layer


class TransformsWidget(QWidget):
    def __init__(self, napari_viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer = napari_viewer
        self._selected_layer = None

        self._name_widget = NameWidget()
        self._scale_widget = ScaleWidget()
        self._translate_widget = TranslateWidget()
        self._rotate_widget = RotateWidget()
        self._shear_widget = ShearWidget()
        self._affine_widget = AffineWidget()

        scale = _Collapsible("scale", self._scale_widget)
        translate = _Collapsible("translate", self._translate_widget)
        rotate = _Collapsible("rotate", self._rotate_widget)
        shear = _Collapsible("shear", self._shear_widget)
        affine = _Collapsible("affine", self._affine_widget)
        for w in (scale, translate, rotate, shear, affine):
            w.expand(animate=False)

        layout = QVBoxLayout()
        layout.addWidget(self._name_widget)
        layout.addWidget(scale)
        layout.addWidget(translate)
        layout.addWidget(rotate)
        layout.addWidget(shear)
        layout.addWidget(affine)
        self.setLayout(layout)

        self._viewer.layers.selection.events.changed.connect(
            self._on_selected_layers_changed
        )
        self._viewer.dims.events.axis_labels.connect(
            self._on_axis_labels_changed
        )
        self._name_widget.apply_all_layers.clicked.connect(
            self._on_apply_clicked
        )

        self._on_selected_layers_changed()

    def _on_selected_layers_changed(self) -> None:
        layer = None
        if len(self._viewer.layers.selection) == 1:
            layer = next(iter(self._viewer.layers.selection))

        if layer == self._selected_layer:
            return

        if self._selected_layer is not None:
            self._selected_layer.events.name.disconnect(
                self._name_widget.on_layer_name_changed
            )

        if layer is not None:
            layer.events.name.connect(self._name_widget.on_layer_name_changed)

        self._name_widget.set_layer(layer)
        self._scale_widget.set_layer(layer)
        self._translate_widget.set_layer(layer)
        self._rotate_widget.set_layer(layer)
        self._shear_widget.set_layer(layer)
        self._affine_widget.set_layer(layer)
        self._selected_layer = layer

        self._on_axis_labels_changed()

    def _on_axis_labels_changed(self) -> None:
        layer = self._selected_layer
        if layer is None:
            return
        layer_axes = self._viewer.dims.axis_labels[-layer.ndim :]
        for w in (
            self._scale_widget,
            self._translate_widget,
            self._rotate_widget,
            self._shear_widget,
            self._affine_widget,
        ):
            w.setAxes(layer_axes)

    # TODO: make this a slot
    def _on_apply_clicked(self, event) -> None:
        if self._selected_layer is None:
            return
        similar_layers = (
            layer
            for layer in self._viewer.layers
            if layer.ndim == self._selected_layer.ndim
        )
        for layer in similar_layers:
            layer.scale = self._selected_layer.scale
            layer.translate = self._selected_layer.translate
            layer.rotate = self._selected_layer.rotate
            layer.shear = self._selected_layer.shear
            layer.affine = self._selected_layer.affine


class NameWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layer_layout = QHBoxLayout()

        label = QLabel("Selected layer:")
        self._edit = QLineEdit()
        self._edit.setPlaceholderText(
            "Select a layer from napari's layer list"
        )
        self._edit.setReadOnly(True)
        layer_layout.addWidget(label)
        layer_layout.addWidget(self._edit)

        self.apply_all_layers = QPushButton("Apply to similar layers")

        layout = QVBoxLayout()
        layout.addLayout(layer_layout)
        layout.addWidget(self.apply_all_layers)
        self.setLayout(layout)

    def set_layer(self, layer: Optional["Layer"]) -> None:
        name = layer.name if layer else ""
        self._edit.setText(name)

    def on_layer_name_changed(self, event) -> None:
        self._edit.setText(event.source.name)


class _Collapsible(QCollapsible):
    def __init__(
        self, title: str, widget: QWidget, parent: Optional[QWidget] = None
    ):
        super().__init__(title, parent)
        self.addWidget(widget)
        layout = self.layout()
        assert layout is not None
        layout.setContentsMargins(0, 0, 0, 0)


class TranslateWidget(VectorEdit):
    def __init__(self) -> None:
        super().__init__()
        self._layer = None
        self.arrayChanged.connect(self._on_array_changed)

    def set_layer(self, layer: Optional["Layer"]) -> None:
        if layer is self._layer:
            return
        old_layer = self._layer
        if old_layer is not None:
            old_layer.events.translate.disconnect(
                self._on_layer_translate_changed
            )
        if layer is not None:
            self._set_array(layer.affine.translate)
            layer.events.translate.connect(self._on_layer_translate_changed)
        self._layer = layer

    def _set_array(self, array: np.ndarray) -> None:
        self.setArray(array)

    def _on_array_changed(self, array: np.ndarray) -> None:
        if self._layer is not None:
            with self._layer.events.translate.blocker(
                self._on_layer_translate_changed
            ):
                self._layer.translate = array

    def _on_layer_translate_changed(self) -> None:
        self._set_array(self._layer.translate)


class ScaleWidget(VectorEdit):
    def __init__(self) -> None:
        super().__init__()
        self._layer = None
        self.arrayChanged.connect(self._on_array_changed)

    def set_layer(self, layer: Optional["Layer"]) -> None:
        if layer is self._layer:
            return
        old_layer = self._layer
        if old_layer is not None:
            old_layer.events.scale.disconnect(self._on_layer_scale_changed)
        if layer is not None:
            self._set_array(layer.affine.scale)
            layer.events.scale.connect(self._on_layer_scale_changed)
        self._layer = layer

    def _set_array(self, array: np.ndarray) -> None:
        self.setArray(array)

    def _on_array_changed(self, array: np.ndarray) -> None:
        if self._layer is not None:
            with self._layer.events.scale.blocker(
                self._on_layer_scale_changed
            ):
                self._layer.scale = array

    def _on_layer_scale_changed(self) -> None:
        self._set_array(self._layer.scale)


class RotateWidget(MatrixEdit):
    def __init__(self) -> None:
        super().__init__()
        self._layer = None
        self.arrayChanged.connect(self._on_array_changed)

    def set_layer(self, layer: Optional["Layer"]) -> None:
        if layer is self._layer:
            return
        old_layer = self._layer
        if old_layer is not None:
            old_layer.events.rotate.disconnect(self._on_layer_rotate_changed)
        if layer is not None:
            self._set_array(layer.rotate)
            layer.events.rotate.connect(self._on_layer_rotate_changed)
        self._layer = layer

    def _set_array(self, array: np.ndarray) -> None:
        self.setArray(array)

    def _on_array_changed(self, array: np.ndarray) -> None:
        if self._layer is not None:
            with self._layer.events.rotate.blocker(
                self._on_layer_rotate_changed
            ):
                self._layer.rotate = array

    def _on_layer_rotate_changed(self) -> None:
        self._set_array(self._layer.rotate)


class ShearWidget(MatrixEdit):
    def __init__(self) -> None:
        super().__init__()
        self._layer = None
        self.arrayChanged.connect(self._on_array_changed)

    def set_layer(self, layer: Optional["Layer"]) -> None:
        if layer is self._layer:
            return
        old_layer = self._layer
        if old_layer is not None:
            old_layer.events.shear.disconnect(self._on_layer_shear_changed)
        if layer is not None:
            shear = _shear_matrix(layer)
            self._set_array(shear)
            layer.events.shear.connect(self._on_layer_shear_changed)
        self._layer = layer

    def _set_array(self, array: np.ndarray) -> None:
        editable = np.zeros(array.shape, dtype=bool)
        editable[np.triu_indices(array.shape[0], 1)] = True
        self.setArray(array, editable=editable)

    def _on_array_changed(self, array: np.ndarray) -> None:
        if self._layer is not None:
            with self._layer.events.shear.blocker(
                self._on_layer_shear_changed
            ):
                self._layer.shear = array

    def _on_layer_shear_changed(self) -> None:
        # Shear can be the upper triangle values (in a vector)
        # or the matrix itself. Always make it a matrix.
        shear = _shear_matrix(self._layer)
        self._set_array(shear)


def _shear_matrix(layer: "Layer") -> np.ndarray:
    shear = layer.shear
    ndim = layer.ndim
    if shear.ndim == 1:
        shear_matrix = np.eye(ndim)
        shear_matrix[np.triu_indices(ndim, k=1)] = shear
        return shear_matrix
    return shear


class AffineWidget(MatrixEdit):
    def __init__(self) -> None:
        super().__init__()
        self._layer = None
        self.arrayChanged.connect(self._on_array_changed)

    def set_layer(self, layer: Optional["Layer"]) -> None:
        if layer is self._layer:
            return
        old_layer = self._layer
        if old_layer is not None:
            old_layer.events.affine.disconnect(self._on_layer_affine_changed)
        if layer is not None:
            self._set_array(layer.affine.affine_matrix)
            layer.events.affine.connect(self._on_layer_affine_changed)
        self._layer = layer

    def setAxes(self, axes: Tuple[str, ...]) -> None:
        # For homogeneous coordinate.
        super().setAxes(axes + ("",))

    def _set_array(self, array: np.ndarray) -> None:
        editable = np.ones(array.shape, dtype=bool)
        editable[-1, :] = False
        self.setArray(array, editable=editable)

    def _on_array_changed(self, array: np.ndarray) -> None:
        if self._layer is not None:
            with self._layer.events.affine.blocker(
                self._on_layer_affine_changed
            ):
                self._layer.affine = array

    def _on_layer_affine_changed(self) -> None:
        axes = self.getAxes()
        self._set_array(self._layer.affine.affine_matrix)
        super().setAxes(axes)
