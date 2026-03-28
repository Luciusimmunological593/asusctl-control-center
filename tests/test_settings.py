from pathlib import Path

from asus_linux_control_center.settings import SettingsStore


def test_settings_roundtrip(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path / "settings.json")
    settings = store.load()
    settings.last_page = "graphics"
    settings.aura_color_1 = "#112233"
    settings.custom_curves["cpu"] = [10, 20, 30, 40, 50, 60, 70, 80]
    store.save(settings)

    reloaded = store.load()
    assert reloaded.last_page == "graphics"
    assert reloaded.aura_color_1 == "#112233"
    assert reloaded.custom_curves["cpu"] == [10, 20, 30, 40, 50, 60, 70, 80]


def test_settings_load_missing_file(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path / "nonexistent.json")
    settings = store.load()
    assert settings.last_page == "overview"
    assert settings.window_width == 1440


def test_settings_load_corrupted_json(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{this is not valid json!!!}", encoding="utf-8")
    store = SettingsStore(path)
    settings = store.load()
    # Should fall back to defaults without crashing
    assert settings.last_page == "overview"
    assert settings.window_width == 1440


def test_settings_load_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("", encoding="utf-8")
    store = SettingsStore(path)
    settings = store.load()
    assert settings.last_page == "overview"


def test_settings_load_partial_keys(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"last_page": "battery"}', encoding="utf-8")
    store = SettingsStore(path)
    settings = store.load()
    assert settings.last_page == "battery"
    assert settings.window_width == 1440  # default for missing key


def test_settings_load_non_integer_dimensions(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"window_width": "not_a_number", "window_height": null}', encoding="utf-8")
    store = SettingsStore(path)
    settings = store.load()
    # Should fall back to defaults without crashing
    assert settings.window_width == 1440
    assert settings.window_height == 920


def test_settings_load_empty_custom_curves(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"custom_curves": {}}', encoding="utf-8")
    store = SettingsStore(path)
    settings = store.load()
    # Empty dict is falsy, so should use defaults
    assert "cpu" in settings.custom_curves


def test_settings_save_creates_parent_dirs(tmp_path: Path) -> None:
    path = tmp_path / "deep" / "nested" / "settings.json"
    store = SettingsStore(path)
    settings = store.load()
    store.save(settings)
    assert path.exists()
