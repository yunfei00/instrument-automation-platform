"""Reusable Qt engineering-unit input widgets for instrument settings."""

from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QWidget

from .units import FREQUENCY_UNITS, TIME_UNITS, best_unit, from_base, to_base


class UnitValueEdit(QWidget):
    """One numeric text field plus an engineering-unit selector.

    The widget exposes SI/base values to Operations while keeping the displayed
    number short and easy to read. It intentionally contains no SCPI logic.
    """

    def __init__(
        self,
        units: Mapping[str, float],
        *,
        default_unit: str,
        zero_unit: str | None = None,
        placeholder: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        if default_unit not in units:
            raise ValueError(f"Unknown default unit: {default_unit}")
        self._units = dict(units)
        self._zero_unit = zero_unit or default_unit

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.edit = QLineEdit(self)
        self.edit.setPlaceholderText(placeholder)
        layout.addWidget(self.edit, 1)

        self.unit_combo = QComboBox(self)
        self.unit_combo.addItems(tuple(self._units.keys()))
        self.unit_combo.setCurrentText(default_unit)
        self.unit_combo.setMinimumWidth(72)
        layout.addWidget(self.unit_combo)

    @classmethod
    def frequency(
        cls,
        *,
        default_unit: str = "MHz",
        zero_unit: str | None = None,
        placeholder: str = "",
        parent: QWidget | None = None,
    ) -> "UnitValueEdit":
        return cls(
            FREQUENCY_UNITS,
            default_unit=default_unit,
            zero_unit=zero_unit or default_unit,
            placeholder=placeholder,
            parent=parent,
        )

    @classmethod
    def time(
        cls,
        *,
        default_unit: str = "ms",
        zero_unit: str | None = None,
        placeholder: str = "",
        parent: QWidget | None = None,
    ) -> "UnitValueEdit":
        return cls(
            TIME_UNITS,
            default_unit=default_unit,
            zero_unit=zero_unit or default_unit,
            placeholder=placeholder,
            parent=parent,
        )

    def base_value_or_blank(self) -> float | str:
        """Return SI/base float, or an empty string when the field is blank."""
        text = self.edit.text().strip()
        if not text:
            return ""
        try:
            displayed = float(text)
        except ValueError as exc:
            raise ValueError("数值必须是数字") from exc
        return to_base(displayed, self.unit_combo.currentText(), self._units)

    def set_base_value(self, value: float, *, auto_unit: bool = True) -> None:
        """Display one SI/base value, optionally choosing a readable unit."""
        numeric = float(value)
        if auto_unit:
            unit = best_unit(numeric, self._units, zero_unit=self._zero_unit)
            self.unit_combo.setCurrentText(unit)
        else:
            unit = self.unit_combo.currentText()
        displayed = from_base(numeric, unit, self._units)
        self.edit.setText(f"{displayed:.12g}")

    def clear(self) -> None:
        self.edit.clear()
