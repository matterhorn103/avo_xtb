# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of py-xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

"""Setup plugin, load settings and detect binaries then expose them as variables."""

import json
import os
import platform
import sys
from pathlib import Path
from shutil import which

# Temporary fix to make sure stdout stream is always Unicode, as Avogadro 1.99 expects
sys.stdout.reconfigure(encoding="utf-8")

# Use OS-appropriate data location to store everything related to the plugin
# Could use platformdirs for this:
# from platformdirs import user_data_dir
# plugin_dir = Path(user_data_dir("py-xtb"))
# ...but since we seem to be able to make do without any other dependencies,
# let's just hard-code it for now
if os.environ.get("XDG_DATA_HOME") is not None:
    plugin_dir = Path(os.environ.get("XDG_DATA_HOME")) / "py-xtb"
elif platform.system() == "Windows":
    plugin_dir = Path.home() / "AppData/Local/py-xtb"
elif platform.system() == "Darwin":
    plugin_dir = Path.home() / "Library/Application Support/py-xtb"
else:
    plugin_dir = Path.home() / ".local/share/py-xtb"

# Create if it doesn't exist yet
if not plugin_dir.exists():
    plugin_dir.mkdir()

# Look for config file in plugin directory
if (plugin_dir / "config.json").exists():
    config_file = plugin_dir / "config.json"
    init = False
# Failing that, try in home directory
elif (Path.home() / "xtb/config.json").exists():
    config_file = Path.home() / "xtb/config.json"
    init = False
# If neither exist, must be first use, so load defaults from this directory
else:
    config_file = Path(__file__).with_name("default_config.json")
    init = True

# Load configuration
with open(config_file, encoding="utf-8") as configuration:
    config = json.load(configuration)

# Make sure that any config options added in later versions of the
# plugin are in config even if they weren't in the config.json file
for option, default in (
    ("solvent", None),
    ("energy_units", "kJ/mol"),
    ("method", 2),
    ("opt_lvl", "normal"),
):
    if option not in config:
        config[option] = default


# If this is first run, determine a suitable place for config and calculations
if init:
    # Test if user has write permission to plugin directory
    # If so we can use it
    try:
        calc_dir = plugin_dir / "last"
        calc_dir.mkdir(parents=True, exist_ok=True)
        with open((calc_dir / "probe.txt"), "w", encoding="utf-8") as probe_file:
            probe_file.write(
                "This file is created only to check everything works.\nIt will be deleted when the first calculation is run."
            )
        config["calc_dir"] = str(calc_dir)
    # If we don't have write permission, use user's home instead, in cross-platform way
    except PermissionError:
        calc_dir = Path.home() / "avo_xtb/last"
        calc_dir.mkdir(parents=True, exist_ok=True)
        config["calc_dir"] = str(calc_dir)
    # Save the initialized configuration to a new config file
    with open(
        (calc_dir.parent / "config.json"), "w", encoding="utf-8"
    ) as new_config_path:
        json.dump(config, new_config_path, indent=2)
        config_file = new_config_path


# Most user options read by other modules should be stored in config;
# that way only the config dictionary has to be loaded.
# The locations of the directories and binaries are better as variables
# because they are Path objects and would otherwise have to be converted
# from strings to Paths every time they are accessed.

# Get the calculation directory for non-new users
if "calc_dir" in config:
    calc_dir = Path(config["calc_dir"])
# If this isn't the first run there really shouldn't be a need for an else
# But just in case
else:
    calc_dir = Path(plugin_dir / "last")

# Create calculation directory if it doesn't yet exist
if not calc_dir.exists():
    calc_dir.mkdir()


# Define functions to find the binaries if not already specified
def find_xtb():
    """Return path to xtb binary as Path object, or None"""
    if (plugin_dir / "xtb/bin").exists():
        xtb_bin = plugin_dir / "xtb/bin/xtb"
        if platform.system() == "Windows":
            xtb_bin = xtb_bin.with_suffix(".exe")
    else:
        # Check PATH
        xtb_bin = which("xtb")
        if xtb_bin is not None:
            xtb_bin = Path(xtb_bin)
    return xtb_bin


def find_crest():
    """Return path to crest binary as Path object, or None"""
    if (plugin_dir / "crest/crest").exists():
        crest_bin = plugin_dir / "crest/crest"
    elif (plugin_dir / "crest").exists():
        crest_bin = plugin_dir / "crest"
    elif (plugin_dir / "xtb/bin/crest/crest").exists():
        crest_bin = plugin_dir / "xtb/bin/crest/crest"
    elif (plugin_dir / "xtb/bin/crest").exists():
        crest_bin = plugin_dir / "xtb/bin/crest"
    # Currently there is no Windows binary for crest but let's assume there will be one day
    elif (plugin_dir / "xtb/bin/crest.exe").exists():
        crest_bin = plugin_dir / "xtb/bin/crest.exe"
    else:
        # Check PATH
        crest_bin = which("crest")
        if crest_bin is not None:
            crest_bin = Path(crest_bin)
    return crest_bin



# Initialize and find the various binaries
# Confirm that those loaded from the config can be found
# If not, do the same search
# Each bin will be set to None if nothing found anywhere
# Note that the binary paths are not saved to the config unless they are
# changed in the Configure... dialog
if "xtb_bin" in config:
    xtb_bin = Path(config["xtb_bin"])
    if not xtb_bin.exists():
        xtb_bin = find_xtb()
else:
    xtb_bin = find_xtb()
if "crest_bin" in config:
    crest_bin = Path(config["crest_bin"])
    if not crest_bin.exists():
        crest_bin = find_crest()
else:
    crest_bin = find_crest()


# Have to set environment variable XTBPATH so that parameterization of GFN0-xTB is found
if xtb_bin is not None:
    os.environ["XTBPATH"] = str(xtb_bin.parent.parent / "share/xtb")
