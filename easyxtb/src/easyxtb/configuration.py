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


logger = logging.getLogger(__name__)

# Current version of package
# Hard code for now, obviously not ideal though
easyxtb_VERSION = "0.10.0"

# File containing the default configuration for new users
default_config_file = Path(__file__).with_name("default_config.json")


def _load_paths():
    global CALCS_DIR
    global TEMP_DIR
    global BIN_DIR
    # User can customize the directory used as directory for the calculations
    # Don't use `tmp` or similar because it doesn't usually persist between reboots
    if "calcs_dir" in config:
        CALCS_DIR = Path(config["calcs_dir"]).resolve()
        logger.debug("Using custom calculations directory from user config")
    else:
        CALCS_DIR = Path(PLUGIN_DIR) / "calcs"
    logger.debug(f"{CALCS_DIR=}")
    # Use the same directory by default for each new calc, overwriting the old one, to avoid
    # build-up of lots of files
    TEMP_DIR = CALCS_DIR / "last"
    logger.debug(f"{TEMP_DIR=}")

    # Check file writing works fine
    try:
        # Create both the TEMP_DIR and the parent CALCS_DIR at the same time if they don't exist
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        if init:
            with open((TEMP_DIR / "probe.txt"), "w", encoding="utf-8") as probe_file:
                probe_file.write(
                    "This file is created only to check everything works.\nIt will be deleted when the first calculation is run."
                )
            config["calcs_dir"] = str(CALCS_DIR)
        logger.debug("Write permission for CALCS_DIR confirmed")
    except Exception as e:
        logger.error(e.message)
        print(e.message)
        raise e
    
    # Define location used to store the binaries on system if their locations are not
    # provided by the user in config
    BIN_DIR = PLUGIN_DIR / "bin"
    logger.debug(f"{BIN_DIR=}")
    BIN_DIR.mkdir(parents=True, exist_ok=True)

def reload_paths():
    _load_paths()

def _update_config():
    """Ensure that any config options added in later versions of the package are in
    config even if they weren't in the config.json file."""
    logger.debug("Making sure that user config is up-to-date with all necessary options")
    with open(default_config_file, encoding="utf-8") as f:
        default_config = json.load(f)
    for option, default in default_config.items():
        if option not in config:
            config[option] = default
            logger.debug(
                f"User config does not contain setting for {option}, so has been set to {default}"
            )
    if "calc_dir" in config:
        config["calcs_dir"] = config["calc_dir"]
        del config["calc_dir"]
    # Record which version was used last
    config["version"] = easyxtb_VERSION
    save_config()

def save_config():
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    logger.debug(f"User config saved to {config_file}")

def _determine_threads() -> int:
    """Work out a sensible number of threads to use for calculations."""
    n_threads = os.cpu_count()
    # Leave more spare cores the more there are available
    sensible_threads = int(n_threads // 1.3)
    return sensible_threads

# Now for everything that should run when the module is loaded

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
        + f"Please choose a suitable data directory, and add its path to {PLUGIN_DIR/'config.json'} under 'calcs_dir'."
    )
    logger.error(error_msg)
    print(error_msg)
    raise PermissionError(error_msg)
_load_paths()
# Save the initialized configuration to a new config file
if init:
    save_config()
if "version" not in config or config["version"] != easyxtb_VERSION:
    _update_config()
# If user hasn't set the number of threads, pick one for them
if config["n_proc"] is None:
    config["n_proc"] = _determine_threads()
