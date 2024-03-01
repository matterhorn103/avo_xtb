# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of avo_xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

"""Setup plugin, load settings and detect binaries then expose them as variables."""

import argparse
import json
import platform
import sys
from pathlib import Path
from shutil import which

# Temporary fix to make sure stdout stream is always Unicode, as Avogadro 1.99 expects
sys.stdout.reconfigure(encoding="utf-8")

plugin_dir = Path(__file__).parent

# Look for config file in plugin directory
if (plugin_dir / "config.json").exists():
    config_file = plugin_dir / "config.json"
    init = False
# Failing that, try in home directory
elif (Path.home() / "xtb" / "config.json").exists():
    config_file = Path.home() / "xtb" / "config.json"
    init = False
# If neither exist, must be first use, so load defaults
else:
    config_file = plugin_dir / "default_config.json"
    init = True

# Load configuration
with open(config_file, encoding="utf-8") as configuration:
    config = json.load(configuration)

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
        calc_dir = Path.home() / "avo_xtb" / "last"
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
    if (plugin_dir / "xtb" / "bin").exists():
        xtb_bin = plugin_dir / "xtb" / "bin" / "xtb"
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
    if (plugin_dir / "crest").exists():
        crest_bin = plugin_dir / "crest"
    elif (plugin_dir / "xtb" / "bin" / "crest").exists():
        crest_bin = plugin_dir / "xtb" / "bin" / "crest"
    # Currently there is no Windows binary for crest but let's assume there will be one day
    elif (plugin_dir / "xtb" / "bin" / "crest.exe").exists():
        crest_bin = plugin_dir / "xtb" / "bin" / "crest.exe"
    else:
        # Check PATH
        crest_bin = which("crest")
        if crest_bin is not None:
            crest_bin = Path(crest_bin)
    return crest_bin


def find_obabel():
    """Return path to obabel binary as Path object, or None"""
    # Try to find the version of Open Babel bundled with Avogadro
    # Current directory upon execution of script seems to be the avo "prefix" directory
    # AS OF 12/02/2024 NO LONGER SEEMS TO BE THE CASE
    # TODO: find new way to find Avo's install directory
    # openbabel should be in the Avo bin directory
    if (Path.cwd() / "bin" / "obabel").exists():
        obabel_bin = Path.cwd() / "bin" / "obabel"
    # Or if on Windows
    elif (Path.cwd() / "bin" / "obabel.exe").exists():
        obabel_bin = Path.cwd() / "bin" / "obabel.exe"
    else:
        # Check PATH
        obabel_bin = which("obabel")
        if obabel_bin is not None:
            obabel_bin = Path(obabel_bin)
    return obabel_bin


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
if "obabel_bin" in config:
    obabel_bin = Path(config["obabel_bin"])
    if not obabel_bin.exists():
        obabel_bin = find_obabel()
else:
    obabel_bin = find_obabel()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--print-options", action="store_true")
    parser.add_argument("--run-command", action="store_true")
    parser.add_argument("--display-name", action="store_true")
    parser.add_argument("--lang", nargs="?", default="en")
    parser.add_argument("--menu-path", action="store_true")
    args = parser.parse_args()

    if args.print_options:
        options = {
            "userOptions": {
                "user_dir": {
                    "type": "string",
                    "label": "Run calculations in",
                    "default": str(calc_dir.parent),
                    "order": 3.0,
                },
                "xtb_bin": {
                    "type": "string",
                    "label": "Location of the xtb binary",
                    "default": str(xtb_bin),
                    "order": 1.0,
                },
                "obabel_bin": {
                    "type": "string",
                    "label": "Location of the Open Babel binary",
                    "default": str(obabel_bin),
                    "order": 2.0,
                },
                "solvent": {
                    "type": "stringList",
                    "label": "Solvation",
                    "values": [
                        "none",
                        "acetone",
                        "acetonitrile",
                        "aniline",
                        "benzaldehyde",
                        "benzene",
                        "ch2cl2",
                        "chcl3",
                        "cs2",
                        "dioxane",
                        "dmf",
                        "dmso",
                        "ether",
                        "ethylacetate",
                        "furane",
                        "hexandecane",
                        "hexane",
                        "methanol",
                        "nitromethane",
                        "octanol",
                        "woctanol",
                        "phenol",
                        "toluene",
                        "thf",
                        "water",
                    ],
                    "default": 0,
                    "order": 5.0,
                },
                "energy_units": {
                    "type": "stringList",
                    "label": "Preferred energy units",
                    "values": ["kJ/mol", "kcal/mol"],
                    "default": 0,
                    "order": 4.0,
                },
                "warning": {
                    "type": "text",
                    "label": "Note",
                    "default": "Changes here will only affect other\nmenus after restarting Avogadro!",
                    "order": 10.0,
                },
            }
        }
        # Make solvation default if found in user config
        if config["solvent"] is not None:
            options["userOptions"]["solvent"]["default"] = config["solvent"]
        # Make energy units displayed match that found in user config
        options["userOptions"]["energy_units"]["default"] = config["energy_units"]
        print(json.dumps(options))
    if args.display_name:
        print("Configure…")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){20}")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())

        # Save change to user_dir if there has been one
        if avo_input["user_dir"] != str(calc_dir.parent):
            calc_dir = Path(avo_input["user_dir"]) / "last"
            try:
                calc_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                result = {
                    "message": "A folder could not be created at the path specified!"
                }
                # Pass back to Avogadro to display to user
                print(json.dumps(result))
            config["calc_dir"] = str(calc_dir)

        # Save change to xtb_bin if there has been one
        if avo_input["xtb_bin"] != str(xtb_bin):
            xtb_bin = Path(avo_input["xtb_bin"])
            config["xtb_bin"] = str(xtb_bin)

        # Save change to obabel_bin if there has been one
        if avo_input["obabel_bin"] != str(obabel_bin):
            obabel_bin = Path(avo_input["obabel_bin"])
            config["obabel_bin"] = str(obabel_bin)

        # Convert "none" string to Python None
        if avo_input["solvent"] == "none":
            solvent_selected = None
        else:
            solvent_selected = avo_input["solvent"]
        # Save change to solvent if there has been one
        config["solvent"] = solvent_selected

        # Save change to energy units if there has been one
        if avo_input["energy_units"] != config["energy_units"]:
            config["energy_units"] = avo_input["energy_units"]

        with open(config_file, "w", encoding="utf-8") as config_path:
            json.dump(config, config_path, indent=2)
