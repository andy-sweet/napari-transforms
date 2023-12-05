from typing import Callable, List, Optional, Protocol, Tuple

import numpy as np
from qtpy.QtCore import QSize, Qt, Signal
from qtpy.QtGui import QDoubleValidator, QValidator
from qtpy.QtWidgets import (
    QGridLayout,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)


class MatrixEdit(QTableWidget):
    arrayChanged = Signal(object)
    _array: np.ndarray

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._array = np.zeros((0, 0), dtype=float)
        self.cellChanged.connect(self._onCellChanged)

    def setArray(
        self, array: np.ndarray, *, editable: Optional[np.ndarray]
    ) -> None:
        assert array.ndim == 2
        if editable is None:
            editable = np.ones(array.shape, dtype=bool)
        assert editable.shape == array.shape
        self.clear()
        self._array = np.array(array, dtype=float, copy=True)
        self.setRowCount(array.shape[0])
        self.setColumnCount(array.shape[1])
        for r in range(self.rowCount()):
            for c in range(self.columnCount()):
                item = QTableWidgetItem(str(array[r, c]))
                self.setItem(r, c, item)
                flags = item.flags()
                if not editable[r, c]:
                    flags &= ~Qt.ItemFlag.ItemIsEditable
                item.setFlags(flags)
        self.resizeColumnsToContents()

    def getArray(self) -> np.ndarray:
        return self._array

    def _onCellChanged(self, row: int, column: int) -> None:
        if item := self.item(row, column):
            data = item.data(Qt.ItemDataRole.DisplayRole)
            value = float(data)
            self._array[row, column] = value
            self.arrayChanged.emit(self._array)


class CompactLineEdit(QLineEdit):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.editingFinished.connect(self._moveCursorToStart)

    def _moveCursorToStart(self) -> None:
        self.setCursorPosition(0)

    def sizeHint(self) -> QSize:
        return self.minimumSizeHint()


class DoubleLineEdit(CompactLineEdit):
    valueChanged = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._validator = QDoubleValidator()
        self.setValidator(self._validator)
        self.editingFinished.connect(self.valueChanged)

    def minimumSizeHint(self) -> QSize:
        width_hint = self.fontMetrics().horizontalAdvance("1.234567")
        sizeHint = super().minimumSizeHint()
        return QSize(width_hint, sizeHint.height())

    def setText(self, text: str) -> None:
        self.setValue(float(text))

    def setValue(self, value: float) -> None:
        text = str(value)
        state, text, _ = self._validator.validate(text, 0)
        if state != QValidator.State.Acceptable:
            raise ValueError("Value is invalid.")
        if text != self.text():
            super().setText(text)
            self.editingFinished.emit()

    def value(self) -> float:
        return float(self.text())


class ReadOnlyLineEdit(CompactLineEdit):
    def __init__(self, *, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("QLineEdit{background: transparent;}")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def setText(self, text: str) -> None:
        super().setText(text)
        self._moveCursorToStart()


def readonly_lineedit(text: Optional[str] = None) -> QLineEdit:
    widget = ReadOnlyLineEdit()
    if text is not None:
        widget.setText(text)
    return widget


class GridRow(Protocol):
    def widgets() -> Tuple[QWidget, ...]:
        ...


def set_row_visible(row: GridRow, visible: bool) -> None:
    for w in row.widgets():
        w.setVisible(visible)


def update_num_rows(
    *,
    rows: List[GridRow],
    layout: QGridLayout,
    desired_num: int,
    row_factory: Callable[[], GridRow],
) -> None:
    current_num = len(rows)
    # Add any missing widgets.
    for _ in range(desired_num - current_num):
        row = row_factory()
        index = layout.count()
        for col, w in enumerate(row.widgets()):
            layout.addWidget(w, index, col)
        rows.append(row)
    # Remove any unneeded widgets.
    for _ in range(current_num - 1, desired_num - 1, -1):
        row = rows.pop()
        for w in row.widgets():
            layout.removeWidget(w)
