from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "packages"
    / "instrument_lab"
    / "src"
    / "instrument_lab"
    / "gui_control.py"
)


def test_main_workspace_uses_large_generic_and_custom_pages():
    text = SOURCE.read_text(encoding="utf-8")

    assert 'self.workspace_tabs.addTab(generic_page, "通用命令")' in text
    assert 'self.workspace_tabs.addTab(custom_page, "定制控制")' in text
    assert "_build_instrument_panel_dock" not in text
    assert "QDockWidget(\"仪表控制 / Instrument Control\"" not in text


def test_advanced_operations_dock_is_hidden_by_default():
    text = SOURCE.read_text(encoding="utf-8")

    assert "dock.hide()" in text
    assert 'toggle_action.setText("高级 Instrument Operations")' in text


def test_fsw_panel_is_routed_from_dedicated_page():
    text = SOURCE.read_text(encoding="utf-8")

    assert "from .gui_fsw import FSWControlPanel" in text
    assert 'definition.panel_type == "fsw"' in text
    assert "panel = FSWControlPanel(self.panel_container)" in text
