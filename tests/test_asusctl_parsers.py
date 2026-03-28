from asus_linux_control_center.backends.asusctl import (
    parse_fan_curve_output,
    parse_help_commands,
    parse_info_output,
    parse_profile_get_output,
    parse_profile_list_output,
)


def test_parse_info_output() -> None:
    output = """
asusctl v6.3.5

Software version: 6.3.5
  Product family: ROG Strix
      Board name: G614JV
"""
    info = parse_info_output(output)
    assert info.asusctl_version == "6.3.5"
    assert info.product_family == "ROG Strix"
    assert info.board_name == "G614JV"


def test_parse_profile_output() -> None:
    profile_list = "Quiet\nBalanced\nPerformance\n"
    assert parse_profile_list_output(profile_list) == ["Quiet", "Balanced", "Performance"]

    active, ac_profile, battery_profile = parse_profile_get_output(
        "Active profile: Performance\n\nAC profile Performance\nBattery profile Quiet\n"
    )
    assert active == "Performance"
    assert ac_profile == "Performance"
    assert battery_profile == "Quiet"


def test_parse_fan_curve_output() -> None:
    sample = """
Fan curves for Performance

[
    (
        fan: CPU,
        pwm: (89, 128, 153, 179, 204, 230, 255, 255),
        temp: (40, 63, 67, 71, 75, 79, 83, 87),
        enabled: true,
    ),
    (
        fan: GPU,
        pwm: (89, 128, 153, 179, 204, 230, 255, 255),
        temp: (40, 63, 67, 71, 75, 79, 83, 87),
        enabled: true,
    ),
]
"""
    snapshot = parse_fan_curve_output(sample)
    assert snapshot is not None
    assert snapshot.temps == [40, 63, 67, 71, 75, 79, 83, 87]
    assert snapshot.enabled["cpu"] is True
    assert snapshot.fans["gpu"][-1] == 100


def test_parse_info_output_empty() -> None:
    info = parse_info_output("")
    assert info.asusctl_version == "Unknown"
    assert info.product_family == "Unknown"
    assert info.board_name == "Unknown"


def test_parse_info_output_partial() -> None:
    output = "Product family: TUF\n"
    info = parse_info_output(output)
    assert info.product_family == "TUF"
    assert info.board_name == "Unknown"


def test_parse_profile_list_empty() -> None:
    assert parse_profile_list_output("") == []
    assert parse_profile_list_output("\n\n  \n") == []


def test_parse_profile_get_empty() -> None:
    active, ac, battery = parse_profile_get_output("")
    assert active is None
    assert ac is None
    assert battery is None


def test_parse_fan_curve_output_empty() -> None:
    assert parse_fan_curve_output("") is None
    assert parse_fan_curve_output("No fan curves available") is None


def test_parse_fan_curve_output_single_fan() -> None:
    sample = """
Fan curves for Balanced

[
    (
        fan: CPU,
        pwm: (50, 100, 150, 200),
        temp: (40, 55, 70, 85),
        enabled: false,
    ),
]
"""
    snapshot = parse_fan_curve_output(sample)
    assert snapshot is not None
    assert "cpu" in snapshot.fans
    assert "gpu" not in snapshot.fans
    assert snapshot.enabled["cpu"] is False


def test_parse_help_commands_empty() -> None:
    assert parse_help_commands("") == []
    assert parse_help_commands("No commands section") == []


def test_parse_help_commands_standard() -> None:
    output = """Usage: asusctl aura effect <COMMAND>

Commands:
  static          Set a static color
  breathe         Breathing effect
  pulse           Pulsing effect
  help            Print this message
"""
    commands = parse_help_commands(output)
    assert "static" in commands
    assert "breathe" in commands
    assert "pulse" in commands
    assert "help" in commands


def test_parse_help_commands() -> None:
    output = """
Usage: asusctl aura power [<command>] [<args>]

Commands:
  keyboard          set power states for keyboard zone
  logo              set power states for logo zone
  lightbar          set power states for lightbar zone
"""
    assert parse_help_commands(output) == ["keyboard", "logo", "lightbar"]
