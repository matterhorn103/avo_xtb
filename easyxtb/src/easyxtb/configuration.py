# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""Setup package, load settings and detect binaries, then expose them as variables.

Most user options read by other modules are stored in `config`; that way only the
`config` dict has to be loaded.
The locations of the directories and binaries are made available as constants, however,
because they are `Path` objects and would otherwise have to be converted from `str` to
`Path`s every time they are accessed.
"""

import json
import logging
import os
import platform
from pathlib import Path
from shutil import which


logger = logging.getLogger(__name__)


# Use an OS-appropriate data location to store all data related to the package
# Could use platformdirs for this, but since we seem to be able to make do without any
# other dependencies, let's just hard-code it for now
if os.environ.get("XDG_DATA_HOME") is not None:
    PLUGIN_DIR = Path(os.environ.get("XDG_DATA_HOME")) / "easyxtb"
elif platform.system() == "Windows":
    PLUGIN_DIR = Path.home() / "AppData/Local/easyxtb"
elif platform.system() == "Darwin":
    PLUGIN_DIR = Path.home() / "Library/Application Support/easyxtb"
else:
    PLUGIN_DIR = Path.home() / ".local/share/easyxtb"
logger.debug(f"{PLUGIN_DIR=}")


config_file = PLUGIN_DIR / "config.json"
default_config_file = Path(__file__).with_name("default_config.json")

def save_config():
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    logger.debug(f"User config saved to {config_file}")

# Look for config file in plugin directory
if config_file.exists():
    with open(config_file, encoding="utf-8") as f:
        config = json.load(f)
    logger.debug(f"Loaded config file from {config_file}")
    init = False
# If doesn't exist, must be first use, so load defaults from this directory
else:
    with open(default_config_file, encoding="utf-8") as f:
        config = json.load(f)
    logger.debug("No config file found so using default initial settings")
    init = True


# Test if user has write permission to plugin directory
try:
    PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
    with open((PLUGIN_DIR / "probe.txt"), "w", encoding="utf-8") as probe_file:
        probe_file.write(
            "This file is created only to check everything works.\nIt will be deleted."
        )
    (PLUGIN_DIR / "probe.txt").unlink()
    logger.debug("Write permission for PLUGIN_DIR confirmed")
except PermissionError:
    error_msg = (
        f"easyxtb was expecting to use {PLUGIN_DIR} to write and store calculation results, but you do not seem to have write permission for this.\n"
        + f"Please choose a suitable data directory, and add its path to {PLUGIN_DIR / 'config.json'} under 'calc_dir'."
    )
    logger.error(error_msg)
    print(error_msg)
    raise PermissionError(error_msg)


# User can customize the directory used as temporary directory for the calculations
# Don't use `tmp` or similar because it doesn't usually persist between reboots
if "calc_dir" in config:
    CALC_DIR = Path(config["calc_dir"])
    logger.debug("Using custom calculation directory from user config")
else:
    CALC_DIR = PLUGIN_DIR
logger.debug(f"{CALC_DIR=}")


# Use the same directory by default for each new calc, overwriting the old one, to avoid
# build-up of lots of files
TEMP_DIR = CALC_DIR / "last"
# Create both the TEMP_DIR and the parent CALC_DIR at the same time if they don't exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)
logger.debug(f"{TEMP_DIR=}")


# If this is first run, check file writing works fine
if init:
    try:
        with open((CALC_DIR / "probe.txt"), "w", encoding="utf-8") as probe_file:
            probe_file.write(
                "This file is created only to check everything works.\nIt will be deleted when the first calculation is run."
            )
        config["calc_dir"] = str(CALC_DIR)
        logger.debug("Write permission for CALC_DIR confirmed")
    except Exception as e:
        logger.error(e.message)
        print(e.message)
        raise e
    # Save the initialized configuration to a new config file
    save_config()


# Current version of package
# Hard code for now, obviously not ideal though
easyxtb_VERSION = "0.7.0"

def update_config():
    """Ensure that any config options added in later versions of the package are in
    config even if they weren't in the config.json file."""
    logger.debug("Making sure that user config is up-to-date with all necessary options")
    with open(default_config_file, encoding="utf-8") as f:
        default_config = json.load(f)
    for option, default in default_config.items():
        if option not in config:
            config[option] = default
            logger.debug(f"User config does not contain setting for {option}, so has been set to {default}")
    # Record which version was used last
    config["version"] = easyxtb_VERSION
    save_config()

if "version" not in config or config["version"] != easyxtb_VERSION:
    update_config()


# Define functions used to find the binaries on system if their locations are not
# provided by the user in config
# As of 0.5.0, binaries should either be in the bin folder, or linked to from it, or
# available in system PATH
BIN_DIR = PLUGIN_DIR / "bin"
logger.debug(f"{BIN_DIR=}")
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
    logger.debug(f"xtb binary location determined to be: {xtb}")
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
    logger.debug(f"crest binary location determined to be: {crest}")
    return crest


# Initialize and find the various binaries
# Confirm that those loaded from the config can be found
# Each global variable will be set to None if nothing found anywhere
# Note that the binary paths are not actually saved to the config unless the user
# actively does so
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
    logger.debug(f"{XTB_BIN=}")
    # Have to set environment variable XTBPATH so that parameterizations (e.g. of
    # GFN0-xTB) are found
    os.environ["XTBPATH"] = str(XTB_BIN.parent.parent / "share/xtb")

if CREST_BIN is not None:
    # Resolve any symlinks
    if CREST_BIN.is_symlink():
        CREST_BIN = CREST_BIN.readlink()
    logger.debug(f"{CREST_BIN=}")


def determine_threads() -> int:
    """Work out a sensible number of threads to use for calculations."""
    n_threads = os.cpu_count()
    # Leave more spare cores the more there are available
    sensible_threads = int(n_threads // 1.3)
    return sensible_threads

# If user hasn't set the number of threads, pick one for them
if config["n_proc"] is None:
    config["n_proc"] = determine_threads()
