from typing import Optional, Tuple

import numpy as np
from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QAbstractScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)


class VectorEdit(QTableWidget):
    arrayChanged = Signal(object)
    _array: np.ndarray

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._array = np.zeros((0,), dtype=float)
        self.cellChanged.connect(self._onCellChanged)
        self.verticalHeader().setVisible(False)
        # Based on answer at:
        # https://stackoverflow.com/questions/75025334/remove-empty-space-at-bottom-of-qtablewidget
        self.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents
        )
        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(), QSizePolicy.Policy.Preferred
        )

    def setArray(
        self, array: np.ndarray, *, editable: Optional[np.ndarray] = None
    ) -> None:
        assert array.ndim == 1
        if editable is None:
            editable = np.ones(array.shape, dtype=bool)
        assert editable.shape == array.shape
        self._array = np.array(array, dtype=float, copy=True)

        self.clear()
        self.setRowCount(1)
        self.setColumnCount(array.shape[0])
        for c in range(self.columnCount()):
            item = QTableWidgetItem(str(array[c]))
            self.setItem(0, c, item)
            flags = item.flags()
            if not editable[c]:
                flags &= ~Qt.ItemFlag.ItemIsEditable
            item.setFlags(flags)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def getArray(self) -> np.ndarray:
        return self._array

    def setAxes(self, axes: Tuple[str, ...]) -> None:
        assert len(axes) == len(self._array)
        self.setHorizontalHeaderLabels(axes)

    def _onCellChanged(self, row: int, column: int) -> None:
        assert row == 0
        if item := self.item(0, column):
            data = item.data(Qt.ItemDataRole.DisplayRole)
            value = float(data)
            self._array[column] = value
            self.arrayChanged.emit(self._array)


class MatrixEdit(QTableWidget):
    arrayChanged = Signal(object)
    _array: np.ndarray

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._array = np.zeros((0, 0), dtype=float)
        self.cellChanged.connect(self._onCellChanged)
        self.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents
        )
        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(), QSizePolicy.Policy.Preferred
        )

    def setArray(
        self, array: np.ndarray, *, editable: Optional[np.ndarray] = None
    ) -> None:
        assert array.ndim == 2
        if editable is None:
            editable = np.ones(array.shape, dtype=bool)
        assert editable.shape == array.shape
        self._array = np.array(array, dtype=float, copy=True)

        self.clear()
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
        self.resizeRowsToContents()

    def getArray(self) -> np.ndarray:
        return self._array

    def setAxes(self, axes: Tuple[str, ...]) -> None:
        assert len(axes) == self._array.shape[0] == self._array.shape[1]
        self.setHorizontalHeaderLabels(axes)
        self.setVerticalHeaderLabels(axes)

    def _onCellChanged(self, row: int, column: int) -> None:
        if item := self.item(row, column):
            data = item.data(Qt.ItemDataRole.DisplayRole)
            value = float(data)
            self._array[row, column] = value
            self.arrayChanged.emit(self._array)
