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


def test_fsw_control_panel_uses_left_controls_right_spectrum_layout():
    text = SOURCE.read_text(encoding="utf-8")

    assert "QSplitter(Qt.Orientation.Horizontal" in text
    assert "QScrollArea" in text
    assert "control_scroll.setMaximumWidth(500)" in text
    assert "self.workspace_splitter.setSizes([420, 980])" in text
    assert "self.workspace_splitter.setStretchFactor(1, 1)" in text
    assert 'self.view_tabs.addTab(data_tab, "Spectrum Data View")' in text


def test_fsw_gui_keeps_scpi_out_of_visual_layer():
    text = SOURCE.read_text(encoding="utf-8")

    assert "SENSe:FREQuency" not in text
    assert "INPut:ATTenuation" not in text
    assert "TRACe1:DATA" not in text
    assert "rohde_schwarz.fsw.single_trace" in text
