#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["click>=8.0", "pyyaml>=6.0", "rich>=13.0", "tomlkit>=0.12.0", "pynvim>=0.5.0", "ruamel.yaml>=0.18.0"]
# ///
# The dependency list matches theme-manager.py on purpose: uv keys its cached
# script environments on it, so both scripts share one environment.

"""Render a theme-system app config for a chezmoi modify_ script.

chezmoi passes the current target on stdin and takes the desired contents from
stdout. The desired contents are the repo's base file with the app's own
theme-system module applied to it, using the machine's current theme data. The
module runs against a copy of the base in a throwaway config home, so it never
touches the real config, and its log output goes nowhere near stdout.

Usage (normally only from .chezmoitemplates/theme-modify.sh):

    theme-modify.py APP --base FILE --theme-data FILE [--keep-blocks OWNER]... \
        < current > desired

--keep-blocks OWNER hands the regions another program fences with
`# >>> OWNER NAME block` / `# <<< OWNER NAME block` to that program: the
current file's blocks replace the base's. The base's blocks only seed a file
that has none of OWNER's blocks yet.

With no theme data (no file, or no `theme` key) the base is printed with only
the kept blocks applied. A module error exits non-zero, so chezmoi stops
rather than resetting colors.
"""

import argparse
import configparser
import contextlib
import importlib
import io
import os
import re
import subprocess
import sys
import tempfile
import types
from pathlib import Path

sys.dont_write_bytecode = True  # the modules are imported from chezmoi's source dir

SCRIPTS_DIR = Path(__file__).resolve().parent

# APP -> (module in apps/, class name). The file each module edits comes from
# the module itself (its config_file or theme_file attribute).
APPS = {
    "lazygit": ("lazygit", "LazygitTheme"),
    "starship": ("starship", "StarshipTheme"),
    "bottom": ("bottom", "BottomTheme"),
    "gitui": ("gitui", "GituiTheme"),
    "yazi": ("yazi", "YaziTheme"),
    "clipboard": ("clipboard", "ClipboardTheme"),
    "flameshot": ("flameshot", "FlameshotTheme"),
    "herdr": ("herdr", "HerdrTheme"),
}

# Flameshot keys the app itself changes in normal use. The base only seeds them.
FLAMESHOT_APP_OWNED = {"drawColor"}


class SideEffectBlocked(RuntimeError):
    pass


def _blocked(*args, **kwargs):
    raise SideEffectBlocked(f"theme-modify: external command blocked: {args[:1]!r}")


def load_app_class(module_name: str, class_name: str):
    """Import one app module without running apps/__init__.py.

    apps/__init__.py imports every module (nvim pulls in pynvim, and so on);
    a stub package keeps each modify script to the module it needs.
    """
    sys.path.insert(0, str(SCRIPTS_DIR))
    pkg = types.ModuleType("apps")
    pkg.__path__ = [str(SCRIPTS_DIR / "apps")]
    sys.modules["apps"] = pkg
    return getattr(importlib.import_module(f"apps.{module_name}"), class_name)


def load_theme_data(path: Path) -> dict:
    """Same loading as theme-manager's load_yaml(THEME_DATA)."""
    import yaml

    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


# Per-app state carried over from the current target. The theme-system keeps
# some state only in the file, so the base alone can't reproduce it.


def carry_yazi_flavors(base: str, current: str) -> str:
    """Static themes set only flavor.dark or flavor.light; keep the other one."""
    import tomlkit

    try:
        cur = tomlkit.parse(current).get("flavor", {})
        doc = tomlkit.parse(base)
    except Exception:
        return base
    if "flavor" not in doc:
        return base
    for key in ("dark", "light"):
        if key in cur:
            doc["flavor"][key] = str(cur[key])
    return tomlkit.dumps(doc)


def _read_ini(text: str) -> configparser.RawConfigParser:
    config = configparser.RawConfigParser()
    config.optionxform = str  # type: ignore[assignment]  # Flameshot keys are camelCase
    config.read_string(text)
    return config


def _ini_dict(config: configparser.RawConfigParser) -> dict:
    return {s: dict(config.items(s)) for s in config.sections()}


def merge_flameshot(base: str, current: str) -> str:
    """Flameshot rewrites its own ini, adding keys and changing drawColor.

    Start from the current file so those survive, then lay the base's settings
    over it (app-owned keys only fill gaps). The module sets uiColor after.
    """
    try:
        merged = _read_ini(current)
        base_cfg = _read_ini(base)
    except configparser.Error:
        return base
    for section in base_cfg.sections():
        if not merged.has_section(section):
            merged.add_section(section)
        for key, value in base_cfg.items(section):
            if key in FLAMESHOT_APP_OWNED and merged.has_option(section, key):
                continue
            merged.set(section, key, value)
    out = io.StringIO()
    merged.write(out)
    return out.getvalue()


def flameshot_keep_format(desired: str, current: str) -> str:
    """Flameshot writes key=value and configparser writes key = value. When
    only the formatting differs, keep the current file so status stays clean."""
    try:
        if _ini_dict(_read_ini(desired)) == _ini_dict(_read_ini(current)):
            return current
    except configparser.Error:
        pass
    return desired


def _marked_blocks(text: str, owner: str) -> dict[str, str]:
    """OWNER's marker-fenced blocks in text, keyed by block name."""
    o = re.escape(owner)
    pattern = re.compile(rf"^# >>> {o} (.+?) block$.*?^# <<< {o} \1 block$", re.M | re.S)
    return {m.group(1): m.group(0) for m in pattern.finditer(text)}


def carry_marked_blocks(base: str, current: str, owner: str) -> str:
    """Take OWNER's blocks from the current file, in the base's positions.

    A block the current file lacks was removed by its owner, so it is dropped
    (the way such programs drop one: the gap closes to one blank line). A block
    only the current file has goes at the end, where these programs append.
    If the current file has none of OWNER's blocks, the base keeps its own.
    """
    theirs = _marked_blocks(current, owner)
    if not theirs:
        return base
    for name, block in _marked_blocks(base, owner).items():
        if name in theirs:
            base = base.replace(block, theirs.pop(name), 1)
        else:
            base = re.sub(rf"\n*{re.escape(block)}\n*", "\n\n", base, count=1)
    for block in theirs.values():
        base = base.rstrip("\n") + "\n\n" + block + "\n"
    return base


def keep_trailing_blank_lines(desired: str, current: str) -> str:
    """herdr-radar leaves a blank line at the end when it drops its last block
    and the herdr module trims it; neither is a change worth reporting."""
    return current if current.rstrip("\n") == desired.rstrip("\n") else desired


PREPARE = {"yazi": carry_yazi_flavors, "flameshot": merge_flameshot}
FINALIZE = {"flameshot": flameshot_keep_format, "herdr": keep_trailing_blank_lines}


def render(
    app_name: str, base: str, current: str, theme_data: dict, keep_blocks: tuple[str, ...] = ()
) -> str:
    for owner in keep_blocks:
        base = carry_marked_blocks(base, current, owner)
    if not theme_data.get("theme"):
        return base

    module_name, class_name = APPS[app_name]
    app_class = load_app_class(module_name, class_name)

    if current and app_name in PREPARE:
        base = PREPARE[app_name](base, current)

    with tempfile.TemporaryDirectory(prefix="theme-modify-") as tmp:
        app = app_class(Path(tmp))
        if not app.supports_current_platform():
            return base
        target = getattr(app, "config_file", None) or getattr(app, "theme_file")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(base.encode())

        # No reloads or other commands from inside chezmoi. None of these
        # modules runs any today; this keeps a future one from doing it here.
        app.run_command = lambda *a, **k: True
        app.command_exists = lambda *a, **k: False
        subprocess.Popen = _blocked  # type: ignore[assignment,misc]
        os.system = _blocked  # type: ignore[assignment]

        errors: list[str] = []
        log_error = app.log_error

        def record_error(message: str) -> None:
            errors.append(message)
            log_error(message)

        app.log_error = record_error

        log = io.StringIO()
        try:
            with contextlib.redirect_stdout(log):
                app.apply_theme(theme_data)
        except Exception as e:
            errors.append(f"{type(e).__name__}: {e}")
        if errors:
            sys.stderr.write(log.getvalue())
            raise SystemExit(f"theme-modify: {app_name} module failed: {'; '.join(errors)}")
        if os.environ.get("THEME_MODIFY_DEBUG"):
            sys.stderr.write(log.getvalue())

        desired = target.read_bytes().decode()

    if current and app_name in FINALIZE:
        desired = FINALIZE[app_name](desired, current)
    return desired


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("app", choices=sorted(APPS))
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--theme-data", type=Path, required=True)
    parser.add_argument("--keep-blocks", action="append", default=[], metavar="OWNER")
    args = parser.parse_args()

    # Bytes in and out, so nothing is newline-translated on the way through.
    current = sys.stdin.buffer.read().decode()
    base = args.base.read_bytes().decode()
    desired = render(args.app, base, current, load_theme_data(args.theme_data), tuple(args.keep_blocks))
    sys.stdout.buffer.write(desired.encode())


if __name__ == "__main__":
    main()
