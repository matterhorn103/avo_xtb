# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of py-xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

"""Setup package, load settings and detect binaries, then expose them as variables."""

import json
import os
import platform
import sys
from pathlib import Path
from shutil import which

# Make sure stdout stream is always Unicode, as Avogadro 1.99 expects
sys.stdout.reconfigure(encoding="utf-8")

# Use an OS-appropriate data location to store all data related to the package
# Could use platformdirs for this, but since we seem to be able to make do without any
# other dependencies, let's just hard-code it for now
if os.environ.get("XDG_DATA_HOME") is not None:
    PLUGIN_DIR = Path(os.environ.get("XDG_DATA_HOME")) / "py-xtb"
elif platform.system() == "Windows":
    PLUGIN_DIR = Path.home() / "AppData/Local/py-xtb"
elif platform.system() == "Darwin":
    PLUGIN_DIR = Path.home() / "Library/Application Support/py-xtb"
else:
    PLUGIN_DIR = Path.home() / ".local/share/py-xtb"

# Look for config file in plugin directory
if (PLUGIN_DIR / "config.json").exists():
    config_file = PLUGIN_DIR / "config.json"
    init = False
# If doesn't exist, must be first use, so load defaults from this directory
else:
    config_file = Path(__file__).with_name("default_config.json")
    init = True

# Load configuration
with open(config_file, encoding="utf-8") as f:
    config = json.load(f)

# Current version of package
# Hard code for now, obviously not ideal though
PY_XTB_VERSION = "0.5.0"

def save_config():
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def update_config():
    """Ensure that any config options added in later versions of the package are in
    config even if they weren't in the config.json file"""
    for option, default in (
        ("solvent", None),
        ("energy_units", "kJ/mol"),
        ("method", 2),
        ("opt_lvl", "normal"),
    ):
        if option not in config:
            config[option] = default
    # Record which version was used last
    config["version"] = PY_XTB_VERSION
    save_config()

if "version" not in config or config["version"] != PY_XTB_VERSION:
    update_config()

# Test if user has write permission to plugin directory
try:
    PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
    with open((PLUGIN_DIR / "probe.txt"), "w", encoding="utf-8") as probe_file:
        probe_file.write(
            "This file is created only to check everything works.\nIt will be deleted."
        )
    (PLUGIN_DIR / "probe.txt").unlink()
except PermissionError:
    error_msg = (
        f"py-xtb was expecting to use {PLUGIN_DIR} to write and store calculation results, but you do not seem to have write permission for this.\n"
        + f"Please choose a suitable data directory, and add its path to {PLUGIN_DIR / 'config.json'} under 'calc_dir'."
    )
    print(error_msg)
    raise PermissionError(error_msg)

# User can customize the directory used as temporary directory for the calculations
# Don't use `tmp` or similar because it doesn't usually persist between reboots
if "calc_dir" in config:
    CALC_DIR = Path(config["calc_dir"])
else:
    CALC_DIR = PLUGIN_DIR

# Use the same directory by default for each new calc, overwriting the old one, to avoid
# build-up of lots of files
TEMP_DIR = CALC_DIR / "last"
# Create both the TEMP_DIR and the parent CALC_DIR at the same time if they don't exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# If this is first run, check file writing works fine
if init:
    try:
        with open((CALC_DIR / "probe.txt"), "w", encoding="utf-8") as probe_file:
            probe_file.write(
                "This file is created only to check everything works.\nIt will be deleted when the first calculation is run."
            )
        config["calc_dir"] = str(CALC_DIR)
    except Exception as e:
        print(e.message)
        raise e
    # Save the initialized configuration to a new config file
    save_config()

# Most user options read by other modules should be stored in config; that way only the
# config dictionary has to be loaded.
# The locations of the directories and binaries are better as global variables, however,
# because they are `Path` objects and would otherwise have to be converted from `str` to
# `Path`s every time they are accessed.

# Define functions used to find the binaries on system if their locations are not
# provided by the user in config
# As of 0.5.0, binaries should either be in the bin folder, or linked to from it, or
# available in system PATH
BIN_DIR = PLUGIN_DIR / "bin"
BIN_DIR.mkdir(parents=True, exist_ok=True)


def find_xtb() -> Path | None:
    """Return path to xtb binary as Path object, or None."""
    if (BIN_DIR / "xtb").exists():
        # Normal binary or symlink to it
        xtb = BIN_DIR / "xtb"
    elif (BIN_DIR / "xtb.exe").exists():
        # Windows
        xtb = BIN_DIR / "xtb.exe"
    elif (BIN_DIR / "xtb-dist").exists():
        # Whole xtb distribution folder with nested binary directory
        xtb = BIN_DIR / "xtb-dist/bin/xtb"
        # Or, on Windows
        if platform.system() == "Windows":
            xtb = xtb.with_suffix(".exe")
    elif which("xtb") is not None:
        # Check PATH
        xtb = Path(which("xtb"))
    else:
        xtb = None
    return xtb


def find_crest() -> Path | None:
    """Return path to crest binary as Path object, or None"""
    if (BIN_DIR / "crest").exists():
        crest = BIN_DIR / "crest"
    elif (BIN_DIR / "crest/crest").exists():
        crest = BIN_DIR / "crest/crest"
    # Currently there is no Windows binary for crest but let's assume there will be
    elif (BIN_DIR / "crest.exe").exists():
        crest = BIN_DIR / "crest.exe"
    elif which("crest") is not None:
        # Check PATH
        crest = Path(which("crest"))
    else:
        crest = None
    return crest


# Initialize and find the various binaries
# Confirm that those loaded from the config can be found
# Each global variable will be set to None if nothing found anywhere
# Note that the binary paths are not actually saved to the config unless they are
# actively changed by the user in the Configure... dialog
if "xtb_bin" in config:
    XTB_BIN = Path(config["xtb_bin"])
    if not XTB_BIN.exists():
        XTB_BIN = find_xtb()
else:
    XTB_BIN = find_xtb()
if "crest_bin" in config:
    CREST_BIN = Path(config["crest_bin"])
    if not CREST_BIN.exists():
        CREST_BIN = find_crest()
else:
    CREST_BIN = find_crest()


if XTB_BIN is not None:
    # Resolve any symlinks
    if XTB_BIN.is_symlink():
        XTB_BIN = XTB_BIN.readlink()
    # Have to set environment variable XTBPATH so that parameterizations (e.g. of
    # GFN0-xTB) are found
    os.environ["XTBPATH"] = str(XTB_BIN.parent.parent / "share/xtb")
