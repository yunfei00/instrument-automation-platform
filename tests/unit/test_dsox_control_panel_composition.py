from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "packages"
    / "instrument_lab"
    / "src"
    / "instrument_lab"
    / "gui_dsox_controls.py"
)


def test_dsox_writable_controls_do_not_subclass_stable_main_panel():
    text = SOURCE.read_text(encoding="utf-8")

    assert "class DSOX3000ControlPanel(QWidget):" in text
    assert "class DSOX3000ControlPanel(DSOX3000Panel):" not in text
    assert "self.main_panel = DSOX3000Panel(" in text
    assert "self.writable_controls = DSOX3000WritableControls(" in text


def test_binary_rendering_stays_owned_by_stable_panel():
    text = SOURCE.read_text(encoding="utf-8")

    writable_section = text.split("class DSOX3000WritableControls", 1)[1].split(
        "class DSOX3000ControlPanel", 1
    )[0]
    assert "QPixmap" not in writable_section
    assert "screen_label" not in writable_section
    assert "waveform_plot" not in writable_section
    assert "_last_screenshot_data" not in writable_section
    assert "_last_waveform_times" not in writable_section


def test_dsox_main_panel_uses_left_controls_and_right_instrument_view():
    text = SOURCE.read_text(encoding="utf-8")

    assert "class AspectPixmapLabel(QLabel):" in text
    assert "Qt.AspectRatioMode.KeepAspectRatio" in text
    assert "def _reflow_main_panel_layout" in text
    assert "QSplitter(Qt.Orientation.Horizontal" in text
    assert "left_scroll.setMaximumWidth(500)" in text
    assert "view_tabs.setMinimumSize(680, 500)" in text
    assert "splitter.setSizes([430, 900])" in text
    assert "_reflow_main_panel_layout(self.main_panel)" in text
    assert "panel.screen_label.setMaximumSize" not in text
