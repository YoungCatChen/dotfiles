# /// script
# requires-python = ">=3.14"
# dependencies = ["pydantic>=2"]
# ///
"""Regression tests for dotfiles_macos_settings.

To run these tests, use:
`uv run --script dotfiles_macos_settings_test.py`.
"""

import collections.abc
import pathlib
import tempfile
import unittest
import unittest.mock

import dotfiles_macos_settings as dms


class MemoryPreferences(dms.PreferenceBackend):
    def __init__(self, state: dict[dms.SettingId, dms.CurrentValue]) -> None:
        self.state = state
        self.writes: list[dms.Setting] = []

    def read(self, identifier: dms.SettingId) -> dms.CurrentValue:
        return self.state.get(identifier, dms.CurrentValue.missing())

    def write(self, setting: dms.Setting) -> None:
        self.writes.append(setting)
        self.state[setting.identifier] = dms.CurrentValue(
            True,
            setting.kind,
            setting.value,
            setting.kind.value,
        )


class MemoryDock(dms.DockBackend):
    def __init__(self, items: list[dms.DockItem]) -> None:
        self.items = items
        self.replacements: list[list[dms.DockItem]] = []

    @property
    def available(self) -> bool:
        return True

    def current(self) -> list[dms.DockItem]:
        return self.items

    def replace(self, items: collections.abc.Sequence[dms.DockItem]) -> None:
        self.items = list(items)
        self.replacements.append(self.items)


class ConfigTest(unittest.TestCase):
    def test_typed_fragments_merge_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            app = root / "Available.app"
            app.mkdir()
            (root / "10-base.toml").write_text(
                f"""
version = 1
notes = ["base note"]

[group.shared]
domains = ["com.dummy"]

[group.shared.values]
Shared = true
Same = "group"

[group.host]
scope = "current_host"
domains = ["com.host"]

[group.host.values]
HostGroup = true

[defaults."com.dummy"]
Same = "direct"
Integer = 1
Float = 1.0
Array = ["one", "two"]

[current_host.NSGlobalDomain]
Host = true

[dock]
replace = true
builtins = ["Finder"]
apps = ["{app}"]
folders = []
""",
                encoding="utf-8",
            )
            (root / "20-override.toml").write_text(
                """
[defaults."com.dummy"]
Same = "override"
""",
                encoding="utf-8",
            )

            configuration = dms.Configuration.load_from_dir(root)

            def setting(key: str) -> dms.Setting:
                identifier = dms.SettingId(dms.Scope.USER, "com.dummy", key)
                return configuration.settings[identifier]

            self.assertEqual(setting("Same").value, "override")
            self.assertIs(setting("Integer").kind, dms.ValueKind.INTEGER)
            self.assertIs(setting("Float").kind, dms.ValueKind.FLOAT)
            self.assertEqual(setting("Array").value, ("one", "two"))
            host_group = dms.SettingId(
                dms.Scope.CURRENT_HOST,
                "com.host",
                "HostGroup",
            )
            self.assertIn(host_group, configuration.settings)
            self.assertEqual(configuration.notes, ["base note"])
            self.assertIsNotNone(configuration.dock)
            assert configuration.dock is not None
            self.assertEqual(configuration.dock.apps, [str(app)])

    def test_unknown_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            (root / "10-invalid.toml").write_text(
                "unknown = true\n",
                encoding="utf-8",
            )
            with self.assertRaises(dms.ConfigError):
                dms.Configuration.load_from_dir(root)


class PreferenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.identifier = dms.SettingId(dms.Scope.USER, "com.dummy", "Enabled")
        self.setting = dms.Setting(
            self.identifier,
            dms.ValueKind.BOOLEAN,
            True,
        )

    def test_diff_is_read_only(self) -> None:
        backend = MemoryPreferences(
            {
                self.identifier: dms.CurrentValue(
                    True,
                    dms.ValueKind.BOOLEAN,
                    False,
                    "boolean",
                )
            }
        )
        with unittest.mock.patch("builtins.print") as print_mock:
            result = dms.reconcile_preferences(
                [self.setting], backend, dms.Action.DIFF)

        self.assertEqual(result.changes, 1)
        self.assertEqual(backend.writes, [])
        self.assertIn("false -> true", print_mock.call_args_list[0].args[0])

    def test_apply_writes_and_verifies(self) -> None:
        backend = MemoryPreferences({})

        with unittest.mock.patch("builtins.print"):
            result = dms.reconcile_preferences(
                [self.setting], backend, dms.Action.APPLY
            )

        self.assertEqual(result.changes, 1)
        self.assertEqual(backend.writes, [self.setting])


class DockTest(unittest.TestCase):
    def test_paths_are_the_identity_and_missing_apps_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            app = root / "Available.app"
            app.mkdir()
            old = root / "Old.app"
            old.mkdir()
            config = dms.DockConfig(
                replace=True,
                builtins=["Finder"],
                apps=[str(app), str(root / "Missing.app")],
                folders=[],
            )
            backend = MemoryDock(
                [dms.DockItem(dms.DockSection.APPS, old.resolve())])
            with unittest.mock.patch("builtins.print") as print_mock:
                changed = dms.reconcile_dock(config, backend, dms.Action.APPLY)

            self.assertTrue(changed)
            self.assertEqual(
                [item.identity for item in backend.items],
                [
                    (dms.DockSection.APPS, app.resolve()),
                    (dms.DockSection.APPS, old.resolve()),
                ],
            )
            self.assertTrue(
                any("Missing.app" in call.args[0] for call in print_mock.call_args_list)
            )

    def test_preserved_apps_do_not_trigger_repeated_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            app = root / "Configured.app"
            app.mkdir()
            extra = root / "Unconfigured.app"
            extra.mkdir()
            config = dms.DockConfig(replace=True, apps=[str(app)])
            backend = MemoryDock(
                [
                    dms.DockItem(dms.DockSection.APPS, app.resolve()),
                    dms.DockItem(dms.DockSection.APPS, extra.resolve()),
                ]
            )

            with unittest.mock.patch("builtins.print"):
                changed = dms.reconcile_dock(config, backend, dms.Action.APPLY)

            self.assertFalse(changed)
            self.assertEqual(backend.replacements, [])


if __name__ == "__main__":
    unittest.main()
