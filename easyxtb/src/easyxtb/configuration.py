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
    PLUGIN_DIR = Path(os.environ.get("XDG_DATA_HOME"))/"easyxtb"
elif platform.system() == "Windows":
    PLUGIN_DIR = Path.home()/"AppData/Local/easyxtb"
elif platform.system() == "Darwin":
    PLUGIN_DIR = Path.home()/"Library/Application Support/easyxtb"
else:
    PLUGIN_DIR = Path.home()/".local/share/easyxtb"
logger.debug(f"{PLUGIN_DIR=}")


config_file = PLUGIN_DIR/"config.json"
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
    with open((PLUGIN_DIR/"probe.txt"), "w", encoding="utf-8") as probe_file:
        probe_file.write(
            "This file is created only to check everything works.\nIt will be deleted."
        )
    (PLUGIN_DIR/"probe.txt").unlink()
    logger.debug("Write permission for PLUGIN_DIR confirmed")
except PermissionError:
    error_msg = (
        f"easyxtb was expecting to use {PLUGIN_DIR} to write and store calculation results, but you do not seem to have write permission for this.\n"
        + f"Please choose a suitable data directory, and add its path to {PLUGIN_DIR/'config.json'} under 'calcs_dir'."
    )
    logger.error(error_msg)
    print(error_msg)
    raise PermissionError(error_msg)


# User can customize the directory used as directory for the calculations
# Don't use `tmp` or similar because it doesn't usually persist between reboots
if "calcs_dir" in config:
    CALCS_DIR = Path(config["calcs_dir"])
    logger.debug("Using custom calculations directory from user config")
else:
    CALCS_DIR = Path(PLUGIN_DIR)/"calcs"
logger.debug(f"{CALCS_DIR=}")
# Use the same directory by default for each new calc, overwriting the old one, to avoid
# build-up of lots of files
TEMP_DIR = CALCS_DIR/"last"
logger.debug(f"{TEMP_DIR=}")

# Check file writing works fine
try:
    # Create both the TEMP_DIR and the parent CALCS_DIR at the same time if they don't exist
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    if init:
        with open((TEMP_DIR/"probe.txt"), "w", encoding="utf-8") as probe_file:
            probe_file.write(
                "This file is created only to check everything works.\nIt will be deleted when the first calculation is run."
            )
        config["calcs_dir"] = str(CALCS_DIR)
    logger.debug("Write permission for CALCS_DIR confirmed")
except Exception as e:
    logger.error(e.message)
    print(e.message)
    raise e


# Save the initialized configuration to a new config file
if init:
    save_config()


# Current version of package
# Hard code for now, obviously not ideal though
easyxtb_VERSION = "0.8.1"

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
    if "calc_dir" in config:
        config["calcs_dir"] = config["calc_dir"]
        del config["calc_dir"]
    # Record which version was used last
    config["version"] = easyxtb_VERSION
    save_config()

if "version" not in config or config["version"] != easyxtb_VERSION:
    update_config()


# Define functions used to find the binaries on system if their locations are not
# provided by the user in config
# As of 0.5.0, binaries should either be in the bin folder, or linked to from it, or
# available in system PATH
BIN_DIR = PLUGIN_DIR/"bin"
logger.debug(f"{BIN_DIR=}")
BIN_DIR.mkdir(parents=True, exist_ok=True)


def find_bin(program: str) -> Path | None:
    """Return path to xtb or CREST binary as Path object, or None."""
    bin_name = f"{program}.exe" if platform.system() == "Windows" else program
    bin_path = None
    for possible_location in [
        BIN_DIR/bin_name,  # Normal binary or symlink to it
        BIN_DIR/program/bin_name,  # Old layout for xtb, current for CREST
        BIN_DIR/f"{program}-dist/bin/{bin_name}",  # Whole xtb distribution folder with nested binary directory
    ]:
        if possible_location.exists() and not possible_location.is_dir():
            bin_path = possible_location
            break
    # Otherwise check the PATH
    if not bin_path and which(bin_name) is not None:
        bin_path = Path(which(bin_name))
    logger.debug(f"{bin_name} binary location determined to be: {bin_path}")
    return bin_path


# Initialize and find the various binaries
# Confirm that those loaded from the config can be found
# Each global variable will be set to None if nothing found anywhere
# Note that the binary paths are not actually saved to the config unless the user
# actively does so
if "xtb_bin" in config:
    XTB_BIN = Path(config["xtb_bin"])
    if not XTB_BIN.exists():
        XTB_BIN = find_bin("xtb")
else:
    XTB_BIN = find_bin("xtb")
if "crest_bin" in config:
    CREST_BIN = Path(config["crest_bin"])
    if not CREST_BIN.exists():
        CREST_BIN = find_bin("crest")
else:
    CREST_BIN = find_bin("crest")


if XTB_BIN is not None:
    # Resolve any symlinks
    if XTB_BIN.is_symlink():
        XTB_BIN = XTB_BIN.readlink()
    logger.debug(f"{XTB_BIN=}")
    # Have to set environment variable XTBPATH so that parameterizations (e.g. of
    # GFN0-xTB) are found
    os.environ["XTBPATH"] = str(XTB_BIN.parent.parent/"share/xtb")

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
