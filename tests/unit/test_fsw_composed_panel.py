from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "packages"
    / "instrument_lab"
    / "src"
    / "instrument_lab"
    / "gui_fsw_composed.py"
)
REFERENCE_TRIGGER = (
    ROOT
    / "packages"
    / "instrument_lab"
    / "src"
    / "instrument_lab"
    / "gui_fsw_reference_trigger.py"
)
SCREENSHOT = (
    ROOT
    / "packages"
    / "instrument_lab"
    / "src"
    / "instrument_lab"
    / "gui_fsw_screenshot.py"
)


def test_fsw_composition_keeps_large_surfaces_separate():
    text = SOURCE.read_text(encoding="utf-8")

    assert "class FSWComposedPanel(QWidget):" in text
    assert "self.main_panel = FSWControlPanel" in text
    assert "self.screenshot_panel = FSWScreenshotPanel" in text
    assert "self.reference_trigger_panel = FSWReferenceTriggerControls" in text
    assert 'self.tabs.addTab(self.main_panel, "主控制台")' in text
    assert 'self.tabs.addTab(self.screenshot_panel, "Instrument Screen")' in text
    assert 'self.tabs.addTab(self.reference_trigger_panel, "幅度 / Trigger")' in text


def test_reference_trigger_gui_keeps_scpi_out_of_visual_layer():
    text = REFERENCE_TRIGGER.read_text(encoding="utf-8")

    assert "DISPlay:WINDow" not in text
    assert "TRIGger:SEQuence" not in text
    assert "rohde_schwarz.fsw.read_reference_level" in text
    assert "rohde_schwarz.fsw.configure_video_trigger" in text
    assert "UnitValueEdit.time" in text


def test_fsw_screenshot_gui_keeps_scpi_out_of_visual_layer():
    text = SCREENSHOT.read_text(encoding="utf-8")

    assert "HCOPy:" not in text
    assert "MMEMory:" not in text
    assert '"rohde_schwarz.fsw.screenshot"' in text
    assert "KeepAspectRatio" in text
    assert "QPixmap" in text
