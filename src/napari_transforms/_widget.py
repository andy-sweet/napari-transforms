from typing import TYPE_CHECKING, List, Optional, Tuple

from qtpy.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from napari_transforms._widget_utils import (
    DoubleLineEdit,
    readonly_lineedit,
    set_row_visible,
    update_num_rows,
)

if TYPE_CHECKING:
    from napari.components import ViewerModel
    from napari.layers import Layer


class TransformsWidget(QWidget):
    def __init__(self, napari_viewer: "ViewerModel") -> None:
        super().__init__()
        self._viewer = napari_viewer
        self._selected_layer = None

        self._name_widget = NameWidget()
        self._transform_widget = TransformWidget(napari_viewer)

        layout = QVBoxLayout()
        layout.addWidget(self._name_widget)
        layout.addWidget(self._transform_widget)
        self.setLayout(layout)

        self._viewer.layers.selection.events.changed.connect(
            self._on_selected_layers_changed
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

        self._name_widget.set_selected_layer(layer)
        self._transform_widget.set_selected_layer(layer)
        self._selected_layer = layer


class NameWidget(QGroupBox):
    def __init__(self) -> None:
        super().__init__()

        self.setTitle("Layer name")

        self._edit = QLineEdit()
        self._edit.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self._edit)
        self.setLayout(layout)

    def set_selected_layer(self, layer: Optional["Layer"]) -> None:
        name = layer.name if layer else ""
        self._edit.setText(name)

    def on_layer_name_changed(self, event) -> None:
        self._edit.setText(event.source.name)


class TransformRow:
    def __init__(self) -> None:
        self.name = readonly_lineedit()
        self.scale = DoubleLineEdit()
        self.scale.setValue(1)
        self.translate = DoubleLineEdit()
        self.translate.setValue(0)

    def widgets(self) -> Tuple[QWidget, ...]:
        return (self.name, self.scale, self.translate)


class TransformWidget(QGroupBox):
    """Shows and controls all axes' names and transform parameters."""

    def __init__(self, viewer: "ViewerModel") -> None:
        super().__init__()

        self.setTitle("Transform")

        self._viewer: "ViewerModel" = viewer
        self._layer: Optional["Layer"] = None
        self._rows: List[TransformRow] = []
        layout = QGridLayout()

        layout.addWidget(QLabel("Axis"), 0, 0)
        layout.addWidget(QLabel("Scale"), 0, 1)
        layout.addWidget(QLabel("Translate"), 0, 2)

        self.setLayout(layout)

        self._viewer.dims.events.axis_labels.connect(
            self._on_viewer_dims_axis_labels_changed
        )

    def set_selected_layer(self, layer: Optional["Layer"]) -> None:
        dims = self._viewer.dims
        update_num_rows(
            rows=self._rows,
            layout=self.layout(),
            desired_num=dims.ndim,
            row_factory=self._make_row,
        )

        self._set_axis_names(dims.axis_labels)
        layer_ndim = 0 if layer is None else layer.ndim
        ndim_diff = dims.ndim - layer_ndim
        for i, row in enumerate(self._axis_widgets()):
            set_row_visible(row, i >= ndim_diff)

        old_layer = self._layer
        if old_layer is not None:
            old_layer.events.scale.disconnect(self._on_layer_scale_changed)
            old_layer.events.translate.disconnect(
                self._on_layer_translate_changed
            )
        if layer is not None:
            layer.events.scale.connect(self._on_layer_scale_changed)
            layer.events.translate.connect(self._on_layer_translate_changed)
        self._layer = layer
        if self._layer is not None:
            self._on_layer_scale_changed()
            self._on_layer_translate_changed()

    def _on_viewer_dims_axis_labels_changed(self) -> None:
        self._set_axis_names(self._viewer.dims.axis_labels)

    def _set_axis_names(self, names: Tuple[str, ...]) -> None:
        widgets = self._axis_widgets()
        for name, widget in zip(names, widgets):
            widget.name.setText(name)

    def _on_layer_scale_changed(self) -> None:
        assert self._layer is not None
        scale = self._layer.scale
        widgets = self._layer_widgets()
        for s, w in zip(scale, widgets):
            w.scale.setValue(s)

    def _on_layer_translate_changed(self) -> None:
        assert self._layer is not None
        translate = self._layer.translate
        widgets = self._layer_widgets()
        for t, w in zip(translate, widgets):
            w.translate.setValue(t)

    def _on_scale_changed(self) -> None:
        assert self._layer is not None
        scale = tuple(w.scale.value() for w in self._layer_widgets())
        self._layer.scale = scale

    def _on_translate_changed(self) -> None:
        assert self._layer is not None
        translate = tuple(w.translate.value() for w in self._layer_widgets())
        self._layer.translate = translate

    def _axis_widgets(self) -> Tuple[TransformRow, ...]:
        return tuple(self._rows)

    def _layer_widgets(self) -> Tuple[TransformRow, ...]:
        return (
            ()
            if self._layer is None
            else tuple(self._rows[-self._layer.ndim :])  # noqa
        )

    def _make_row(self) -> TransformRow:
        widget = TransformRow()
        widget.scale.valueChanged.connect(self._on_scale_changed)
        widget.translate.valueChanged.connect(self._on_translate_changed)
        return widget
