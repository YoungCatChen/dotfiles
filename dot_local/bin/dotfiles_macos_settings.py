"""Compare and apply declarative macOS settings from ordered TOML files."""

import argparse
import dataclasses
import enum
import os
import pathlib
import plistlib
import shlex
import shutil
import subprocess
import sys
import urllib.parse
from collections.abc import Sequence
from typing import Final, Literal, Protocol, cast

import pydantic
import tomllib

type PreferenceAtom = bool | int | float | str
type PreferenceValue = PreferenceAtom | list[str]
type StoredValue = PreferenceAtom | tuple[str, ...]
type DockFolder = tuple[
    str,
    Literal["folder", "stack"],
    Literal["auto", "fan", "grid", "list"],
    Literal["name", "dateadded", "datemodified", "datecreated", "kind"],
]

APP_DIRECTORIES: Final = (
    pathlib.Path("/Applications"),
    pathlib.Path("/System/Applications"),
    pathlib.Path("/System/Applications/Utilities"),
)

LOGOUT_DOMAINS: Final = frozenset(
    {
        "NSGlobalDomain",
        "com.apple.Accessibility",
        "com.apple.universalaccess",
        "com.apple.AppleMultitouchTrackpad",
        "com.apple.driver.AppleBluetoothMultitouch.trackpad",
        "com.apple.AppleMultitouchMouse",
        "com.apple.driver.AppleBluetoothMultitouch.mouse",
    }
)


class ConfigError(Exception):
    """The TOML configuration is invalid."""


class CommandError(Exception):
    """A required system command failed."""

    @classmethod
    def from_result(
        cls,
        result: subprocess.CompletedProcess[bytes],
    ) -> CommandError:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        stdout = result.stdout.decode("utf-8", errors="replace").strip()
        message = stderr or stdout
        suffix = f": {message}" if message else ""
        argv = [
            str(argument) for argument in cast(Sequence[object], result.args)
        ]
        return cls(
            f"command failed ({result.returncode}): {shlex.join(argv)}{suffix}"
        )


class Action(enum.StrEnum):
    DIFF = "diff"
    APPLY = "apply"


class Scope(enum.StrEnum):
    USER = "user"
    CURRENT_HOST = "current_host"


class ValueKind(enum.StrEnum):
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    ARRAY = "array"


class DockSection(enum.StrEnum):
    APPS = "persistentApps"
    FOLDERS = "persistentOthers"


class ModelBase(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")


class GroupConfig(ModelBase):
    scope: Scope = Scope.USER
    domains: list[str]
    values: dict[str, PreferenceValue]


class DockConfig(ModelBase):
    replace: Literal[True]
    builtins: list[str] = pydantic.Field(default_factory=list)
    apps: list[str] = pydantic.Field(default_factory=list)
    folders: list[DockFolder] = pydantic.Field(default_factory=list)


class FragmentConfig(ModelBase):
    version: Literal[1] = 1
    notes: list[str] = pydantic.Field(default_factory=list)
    defaults: dict[str, dict[str, PreferenceValue]] = pydantic.Field(
        default_factory=dict
    )
    current_host: dict[str, dict[str, PreferenceValue]] = pydantic.Field(
        default_factory=dict
    )
    group: dict[str, GroupConfig] = pydantic.Field(default_factory=dict)
    dock: DockConfig | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class SettingId:
    scope: Scope
    domain: str
    key: str


@dataclasses.dataclass(frozen=True, slots=True)
class Setting:
    identifier: SettingId
    kind: ValueKind
    value: StoredValue

    @classmethod
    def from_value(
        cls,
        identifier: SettingId,
        value: PreferenceValue,
    ) -> Setting:
        if isinstance(value, list):
            return cls(identifier, ValueKind.ARRAY, tuple(value))
        if type(value) is bool:
            return cls(identifier, ValueKind.BOOLEAN, value)
        if type(value) is int:
            return cls(identifier, ValueKind.INTEGER, value)
        if type(value) is float:
            return cls(identifier, ValueKind.FLOAT, value)
        return cls(identifier, ValueKind.STRING, value)


@dataclasses.dataclass(slots=True)
class Configuration:
    settings: dict[SettingId, Setting] = dataclasses.field(default_factory=dict)
    dock: DockConfig | None = None
    notes: list[str] = dataclasses.field(default_factory=list)
    loaded_files: list[pathlib.Path] = dataclasses.field(default_factory=list)

    def add(self, setting: Setting) -> None:
        self.settings.pop(setting.identifier, None)
        self.settings[setting.identifier] = setting

    def merge_values(
        self,
        scope: Scope,
        domain: str,
        values: dict[str, PreferenceValue],
    ) -> None:
        for key, value in values.items():
            identifier = SettingId(scope, domain, key)
            self.add(Setting.from_value(identifier, value))

    @classmethod
    def load_from_dir(cls, config_dir: pathlib.Path) -> Configuration:
        """Load and merge every TOML fragment in filename order."""
        configuration = cls()
        for path in sorted(config_dir.glob("*.toml")):
            try:
                with path.open("rb") as stream:
                    fragment = FragmentConfig.model_validate(
                        tomllib.load(stream)
                    )
            except (OSError, tomllib.TOMLDecodeError) as error:
                raise ConfigError(f"{path}: {error}") from error
            except pydantic.ValidationError as error:
                raise ConfigError(f"{path}:\n{error}") from error

            configuration.loaded_files.append(path)
            configuration.notes.extend(fragment.notes)
            if fragment.dock:
                configuration.dock = fragment.dock

            for group in fragment.group.values():
                for domain in group.domains:
                    configuration.merge_values(
                        group.scope,
                        domain,
                        group.values,
                    )
            for domain, values in fragment.defaults.items():
                configuration.merge_values(Scope.USER, domain, values)
            for domain, values in fragment.current_host.items():
                configuration.merge_values(
                    Scope.CURRENT_HOST,
                    domain,
                    values,
                )

        return configuration


class SubprocessRunner:
    def __init__(self) -> None:
        self._environment = os.environ.copy()
        self._environment["LC_ALL"] = "C"

    def run(
        self,
        argv: Sequence[str],
        *,
        input_bytes: bytes | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            argv,
            input=input_bytes,
            capture_output=True,
            check=False,
            env=self._environment,
        )


@dataclasses.dataclass(frozen=True, slots=True)
class CurrentValue:
    exists: bool
    kind: ValueKind | None = None
    value: StoredValue | None = None
    raw_type: str | None = None

    @classmethod
    def missing(cls) -> CurrentValue:
        return cls(False)


class PreferenceBackend(Protocol):
    def read(self, identifier: SettingId) -> CurrentValue: ...

    def write(self, setting: Setting) -> None: ...


class DefaultsBackend(PreferenceBackend):
    def __init__(
        self,
        runner: SubprocessRunner,
        defaults_command: str,
        plutil_command: str,
    ) -> None:
        self._runner = runner
        self._defaults = defaults_command
        self._plutil = plutil_command

    def read(self, identifier: SettingId) -> CurrentValue:
        prefix = self._prefix(identifier.scope)
        type_result = self._runner.run(
            [*prefix, "read-type", identifier.domain, identifier.key]
        )
        if type_result.returncode != 0:
            error = (type_result.stderr + type_result.stdout).decode(
                "utf-8", errors="replace"
            )
            if "does not exist" in error:
                return CurrentValue.missing()
            raise CommandError.from_result(type_result)

        raw_type = (
            type_result.stdout.decode("utf-8").strip().removeprefix("Type is ")
        )
        try:
            kind = ValueKind(raw_type)
        except ValueError:
            kind = None
        value_result = self._runner.run(
            [*prefix, "read", identifier.domain, identifier.key]
        )
        if value_result.returncode != 0:
            raise CommandError.from_result(value_result)
        if kind is None:
            value = value_result.stdout.decode("utf-8").removesuffix("\n")
            return CurrentValue(True, None, value, raw_type)
        return CurrentValue(
            True,
            kind,
            self._parse_value(kind, value_result.stdout),
            raw_type,
        )

    def write(self, setting: Setting) -> None:
        flag = {
            ValueKind.BOOLEAN: "-bool",
            ValueKind.INTEGER: "-int",
            ValueKind.FLOAT: "-float",
            ValueKind.STRING: "-string",
            ValueKind.ARRAY: "-array",
        }[setting.kind]
        values = (
            setting.value
            if isinstance(setting.value, tuple)
            else (setting.value,)
        )
        result = self._runner.run(
            [
                *self._prefix(setting.identifier.scope),
                "write",
                setting.identifier.domain,
                setting.identifier.key,
                flag,
                *(format_atom(value) for value in values),
            ]
        )
        if result.returncode != 0:
            raise CommandError.from_result(result)

    def _prefix(self, scope: Scope) -> list[str]:
        if scope is Scope.CURRENT_HOST:
            return [self._defaults, "-currentHost"]
        return [self._defaults]

    def _parse_value(
        self,
        kind: ValueKind,
        output: bytes,
    ) -> StoredValue:
        text = output.decode("utf-8").removesuffix("\n")
        if kind is ValueKind.BOOLEAN:
            return text in {"1", "true", "TRUE", "YES", "yes"}
        if kind is ValueKind.INTEGER:
            return int(text)
        if kind is ValueKind.FLOAT:
            return float(text)
        if kind is ValueKind.STRING:
            return text
        converted = self._runner.run(
            [self._plutil, "-convert", "binary1", "-o", "-", "-"],
            input_bytes=output,
        )
        if converted.returncode != 0:
            raise CommandError.from_result(converted)
        values = plistlib.loads(converted.stdout)
        return tuple(cast(list[str], values))


def format_atom(value: PreferenceAtom) -> str:
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is float:
        return repr(value)
    return str(value)


def format_value(value: StoredValue | None) -> str:
    if isinstance(value, tuple):
        return "[" + ", ".join(format_atom(item) for item in value) + "]"
    return "<unset>" if value is None else format_atom(value)


def matches(current: CurrentValue, setting: Setting) -> bool:
    return (
        current.exists
        and current.kind is setting.kind
        and current.value is not None
        and current.value == setting.value
    )


@dataclasses.dataclass(frozen=True, slots=True)
class PreferenceResult:
    total: int
    changes: int
    changed_domains: frozenset[str]


def reconcile_preferences(
    settings: Sequence[Setting],
    backend: PreferenceBackend,
    action: Action,
) -> PreferenceResult:
    changes: list[tuple[Setting, CurrentValue]] = []
    for setting in settings:
        current = backend.read(setting.identifier)
        if not matches(current, setting):
            changes.append((setting, current))

    marker = "~" if action is Action.DIFF else ">"
    for setting, current in changes:
        current_text = format_value(current.value)
        desired_text = format_value(setting.value)
        if current.exists and current.kind is not setting.kind:
            current_text += f" ({current.raw_type or 'unknown'})"
            desired_text += f" ({setting.kind.value})"
        identifier = setting.identifier
        print(
            f"{marker} {identifier.scope.value} {identifier.domain} "
            f"{identifier.key}: {current_text} -> {desired_text}"
        )

    if action is Action.APPLY:
        for setting, _ in changes:
            backend.write(setting)
        failed = [
            setting.identifier
            for setting, _ in changes
            if not matches(backend.read(setting.identifier), setting)
        ]
        if failed:
            details = ", ".join(
                f"{item.scope.value}:{item.domain}:{item.key}"
                for item in failed
            )
            raise CommandError(f"settings did not match after apply: {details}")

    return PreferenceResult(
        len(settings),
        len(changes),
        frozenset(setting.identifier.domain for setting, _ in changes),
    )


@dataclasses.dataclass(frozen=True, slots=True)
class DockItem:
    section: DockSection
    path: pathlib.Path
    display: str | None = None
    view: str | None = None
    sort: str | None = None

    @property
    def identity(self) -> tuple[DockSection, pathlib.Path]:
        return self.section, self.path

    @property
    def name(self) -> str:
        return (
            self.path.stem
            if self.section is DockSection.APPS
            else self.path.name
        )


def resolve_app(configured_path: str) -> pathlib.Path | None:
    path = pathlib.Path(configured_path).expanduser()
    for directory in APP_DIRECTORIES:
        candidate = directory / path
        if candidate.exists():
            return candidate.resolve()
    return None


def resolve_dock(
    config: DockConfig,
) -> tuple[list[DockItem], list[str]]:
    items: list[DockItem] = []
    missing: list[str] = []

    for configured_path in config.apps:
        path = resolve_app(configured_path)
        if path:
            items.append(DockItem(DockSection.APPS, path))
        else:
            missing.append(configured_path)

    for configured_path, display, view, sort in config.folders:
        path = pathlib.Path(configured_path).expanduser()
        if path.is_dir():
            items.append(
                DockItem(
                    DockSection.FOLDERS,
                    path.resolve(),
                    display,
                    view,
                    sort,
                )
            )
        else:
            missing.append(configured_path)

    return items, missing


class DockBackend(Protocol):
    @property
    def available(self) -> bool: ...

    def current(self) -> list[DockItem]: ...

    def replace(self, items: Sequence[DockItem]) -> None: ...


class DockUtilBackend(DockBackend):
    def __init__(
        self,
        runner: SubprocessRunner,
        command: str | None,
    ) -> None:
        self._runner = runner
        self._command = command

    @property
    def available(self) -> bool:
        return self._command is not None

    def current(self) -> list[DockItem]:
        command = cast(str, self._command)
        result = self._runner.run([command, "--list"])
        if result.returncode != 0:
            raise CommandError.from_result(result)
        items: list[DockItem] = []
        for line in result.stdout.decode("utf-8").splitlines():
            fields = line.split("\t")
            if len(fields) < 3 or fields[2] not in DockSection:
                continue
            url = urllib.parse.urlparse(fields[1])
            raw_path = (
                urllib.parse.unquote(url.path) if url.scheme else fields[1]
            )
            items.append(
                DockItem(
                    DockSection(fields[2]),
                    pathlib.Path(raw_path).expanduser().resolve(strict=False),
                )
            )
        return items

    def replace(self, items: Sequence[DockItem]) -> None:
        command = cast(str, self._command)
        self._check([command, "--remove", "all", "--no-restart"])
        for item in items:
            argv = [command, "--add", str(item.path)]
            if item.section is DockSection.FOLDERS:
                argv.extend(
                    [
                        "--display",
                        cast(str, item.display),
                        "--view",
                        cast(str, item.view),
                        "--sort",
                        cast(str, item.sort),
                    ]
                )
            self._check([*argv, "--no-restart"])

    def _check(self, argv: Sequence[str]) -> None:
        result = self._runner.run(argv)
        if result.returncode != 0:
            raise CommandError.from_result(result)


def dock_identities(
    items: Sequence[DockItem],
) -> list[tuple[DockSection, pathlib.Path]]:
    return [item.identity for item in items]


def reconcile_dock(
    config: DockConfig | None,
    backend: DockBackend,
    action: Action,
) -> bool:
    if config is None:
        return False
    desired, missing = resolve_dock(config)
    for configured_path in missing:
        print(f"! Dock: skipping unavailable item {configured_path}")
    if not backend.available:
        print("! Dock layout requires dockutil; desired order:")
        for name in [*config.builtins, *(item.name for item in desired)]:
            print(f"    {name}")
        return False

    current = backend.current()
    if dock_identities(current) == dock_identities(desired):
        print("= Dock layout")
        return False

    configured_apps = [
        item for item in desired if item.section is DockSection.APPS
    ]
    configured_folders = [
        item for item in desired if item.section is DockSection.FOLDERS
    ]
    configured_app_ids = {item.identity for item in configured_apps}
    unconfigured_apps = [
        item
        for item in current
        if item.section is DockSection.APPS
        and item.identity not in configured_app_ids
        and item.path.exists()
    ]
    applied_order = [
        *configured_apps,
        *unconfigured_apps,
        *configured_folders,
    ]

    print("~ Dock layout")
    print("  current:")
    for item in current:
        print(f"    {item.name}")
    print("  desired (built-ins stay fixed):")
    for name in [*config.builtins, *(item.name for item in desired)]:
        print(f"    {name}")
    if unconfigured_apps:
        print("  unconfigured applications preserved after configured apps:")
        for item in unconfigured_apps:
            print(f"    {item.name}")
    if action is Action.DIFF:
        return False
    if config.apps and not any(
        item.section is DockSection.APPS for item in desired
    ):
        print("! Dock has no available applications; skipped")
        return False
    if dock_identities(current) == dock_identities(applied_order):
        return False
    backend.replace(applied_order)
    if dock_identities(backend.current()) != dock_identities(applied_order):
        raise CommandError("Dock layout did not match after apply")
    return True


def find_command(name: str, *, required: bool) -> str | None:
    path = shutil.which(name)
    if path is None and required:
        raise CommandError(f"command not found: {name}")
    return path


def restart_processes(
    runner: SubprocessRunner,
    killall_command: str | None,
    changed_domains: frozenset[str],
    dock_changed: bool,
) -> None:
    if killall_command is None:
        return
    processes: list[str] = []
    if "com.apple.finder" in changed_domains:
        processes.append("Finder")
    if changed_domains & {
        "com.apple.controlcenter",
        "com.apple.menuextra.clock",
    }:
        processes.extend(["ControlCenter", "SystemUIServer"])
    if "com.apple.dock" in changed_domains or dock_changed:
        processes.append("Dock")
    for process in dict.fromkeys(processes):
        runner.run([killall_command, process])


def get_default_config_dir() -> pathlib.Path:
    if override := os.environ.get("DOTFILES_MACOS_SETTINGS_DIR"):
        return pathlib.Path(override)
    return (
        pathlib.Path(
            os.environ.get("XDG_CONFIG_HOME", pathlib.Path.home() / ".config")
        )
        / "dotfiles-macos-settings"
    )


def run(argv: Sequence[str]) -> int:
    """Run the command and return a process exit status."""
    parser = argparse.ArgumentParser(prog="dotfiles-macos-settings")
    parser.add_argument(
        "action",
        nargs="?",
        choices=[action.value for action in Action],
        default=Action.DIFF.value,
    )
    parser.add_argument(
        "--config-dir",
        type=pathlib.Path,
        default=get_default_config_dir(),
    )
    arguments = parser.parse_args(argv)
    action = Action(arguments.action)
    directory = arguments.config_dir.expanduser()
    configuration = Configuration.load_from_dir(directory)
    if not configuration.loaded_files:
        print(f"No readable configuration found in {directory}")
        return 0
    for path in configuration.loaded_files:
        print(f"Loading {path}")

    defaults = cast(
        str,
        find_command(
            os.environ.get("DOTFILES_MACOS_SETTINGS_DEFAULTS_CMD", "defaults"),
            required=True,
        ),
    )
    plutil = cast(
        str,
        find_command(
            os.environ.get("DOTFILES_MACOS_SETTINGS_PLUTIL_CMD", "plutil"),
            required=True,
        ),
    )
    dockutil = find_command(
        os.environ.get("DOTFILES_MACOS_SETTINGS_DOCKUTIL_CMD", "dockutil"),
        required=False,
    )
    killall = find_command(
        os.environ.get("DOTFILES_MACOS_SETTINGS_KILLALL_CMD", "killall"),
        required=False,
    )

    runner = SubprocessRunner()
    result = reconcile_preferences(
        list(configuration.settings.values()),
        DefaultsBackend(runner, defaults, plutil),
        action,
    )
    dock_changed = reconcile_dock(
        configuration.dock,
        DockUtilBackend(runner, dockutil),
        action,
    )

    if action is Action.DIFF:
        print(
            f"Diff: {result.changes} of {result.total} "
            "defaults settings differ."
        )
    else:
        restart_processes(
            runner,
            killall,
            result.changed_domains,
            dock_changed,
        )
        print(f"Applied {result.changes} of {result.total} defaults settings.")
        if result.changed_domains & LOGOUT_DOMAINS:
            print(
                "Some keyboard, appearance, or input changes may require "
                "logging out."
            )

    if configuration.notes:
        print("Notes:")
        for note in configuration.notes:
            print(f"    {note}")

    return 0


def main() -> int:
    if sys.platform != "darwin":
        print(
            "dotfiles-macos-settings: this command only supports macOS",
            file=sys.stderr,
        )
        return 1
    try:
        return run(sys.argv[1:])
    except (ConfigError, CommandError) as error:
        print(f"dotfiles-macos-settings: {error}", file=sys.stderr)
        return 1
