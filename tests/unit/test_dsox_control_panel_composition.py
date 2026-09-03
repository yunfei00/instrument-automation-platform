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
    assert "screenshot" not in writable_section.lower()
    assert "waveform" not in writable_section.lower()
