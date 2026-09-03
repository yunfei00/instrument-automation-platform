from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "packages"
    / "instrument_lab"
    / "src"
    / "instrument_lab"
    / "gui_fsw.py"
)


def test_fsw_control_panel_uses_left_controls_right_trace_layout():
    text = SOURCE.read_text(encoding="utf-8")

    assert "QSplitter(Qt.Orientation.Horizontal" in text
    assert "QScrollArea" in text
    assert "control_scroll.setMaximumWidth(500)" in text
    assert "self.workspace_splitter.setSizes([420, 980])" in text
    assert "self.workspace_splitter.setStretchFactor(1, 1)" in text
    assert 'self.view_tabs.addTab(data_tab, "Trace Data View")' in text


def test_fsw_gui_supports_frequency_and_zero_span_time_axes():
    text = SOURCE.read_text(encoding="utf-8")

    assert 'axis_kind not in {"frequency", "time"}' in text
    assert 'axis_kind == "time"' in text
    assert 'result.get("times_s")' in text
    assert '["time_s", "level_dbm"]' in text
    assert '["frequency_hz", "level_dbm"]' in text
    assert "Zero Span · Time/Level" in text


def test_fsw_trace_uses_the_full_ten_horizontal_divisions():
    text = SOURCE.read_text(encoding="utf-8")

    assert "for column in range(11):" in text
    assert "column / 10.0" in text
    assert "axis_start = self._axis_values[0]" in text
    assert "axis_stop = self._axis_values[-1]" in text
    assert "x_min, x_max = axis_start, axis_stop" in text
    assert "Horizontal padding made the real trace occupy only nine" in text


def test_fsw_gui_uses_engineering_unit_controls():
    text = SOURCE.read_text(encoding="utf-8")

    assert "from .gui_units import UnitValueEdit" in text
    assert 'UnitValueEdit.frequency(' in text
    assert 'default_unit="MHz"' in text
    assert 'UnitValueEdit.time(' in text
    assert 'default_unit="ms"' in text
    assert '"rohde_schwarz.fsw.set_sweep_time"' in text


def test_fsw_gui_exposes_verified_marker_peak_action():
    text = SOURCE.read_text(encoding="utf-8")

    assert 'QGroupBox("Marker 1")' in text
    assert 'QPushButton("Peak Search")' in text
    assert '"rohde_schwarz.fsw.marker_peak"' in text
    assert "Marker Level" in text


def test_fsw_gui_keeps_scpi_out_of_visual_layer():
    text = SOURCE.read_text(encoding="utf-8")

    assert "SENSe:FREQuency" not in text
    assert "SENSe:SWEep" not in text
    assert "CALCulate1:MARKer1" not in text
    assert "INPut:ATTenuation" not in text
    assert "TRACe1:DATA" not in text
    assert "rohde_schwarz.fsw.single_trace" in text
