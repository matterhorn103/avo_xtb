"""
avo_xtb
A full-featured interface to xtb in Avogadro 2.
Copyright (c) 2023, Matthew J. Milner

BSD 3-Clause License

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import argparse
import json
import platform
import sys
from pathlib import Path
from shutil import which


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
        Path.mkdir(calc_dir, parents=True, exist_ok=True)
        with open((calc_dir / "probe.txt"), "w", encoding="utf-8") as probe_file:
            probe_file.write("This file is created only to check everything works.\nIt will be deleted when the first calculation is run.")
        config["calc_dir"] = str(calc_dir)
    # If we don't have write permission, use user's home instead, in cross-platform way
    except PermissionError:
        calc_dir = Path.home() / "xtb" / "last"
        Path.mkdir(calc_dir, parents=True, exist_ok=True)
        config["calc_dir"] = str(calc_dir)
    # Save the initialized configuration to a new config file
    with open((calc_dir.parent / "config.json"), "w", encoding="utf-8") as new_config_path:
        json.dump(config, new_config_path)
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

# Find xtb
if "xtb_bin" in config:
    xtb_bin = Path(config["xtb_bin"])
elif (plugin_dir / "xtb" / "bin").exists():
    xtb_bin = plugin_dir / "xtb" / "bin" / "xtb"
    if platform.system() == "Windows":
        xtb_bin = xtb_bin.with_suffix(".exe")
else:
    xtb_bin = which("xtb")

# Find crest
if "crest_bin" in config:
    crest_bin = Path(config["crest_bin"])
elif (plugin_dir / "crest").exists():
    crest_bin = plugin_dir / "crest"
elif (plugin_dir / "xtb" / "bin" / "crest").exists():
    crest_bin = plugin_dir / "xtb" / "bin" / "crest"
# Currently there is no Windows binary for crest but let's assume there will be one day
elif (plugin_dir / "xtb" / "bin" / "crest.exe").exists():
    crest_bin = plugin_dir / "xtb" / "bin" / "crest.exe"
else:
    crest_bin = which("crest")



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
                    "order": 2.0
                },
                "xtb_bin": {
                    "type": "string",
                    "label": "Location of the xtb binary",
                    "default": str(xtb_bin),
                    "order": 1.0
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
                        "water"
                        ],
                    "default": 0,
                    "order": 4.0
                },
                "energy_units": {
                    "type": "stringList",
                    "label": "Preferred energy units",
                    "values": ["kJ/mol", "kcal/mol"],
                    "default": 0,
                    "order": 3.0
                },
                "warning": {
                    "type": "text",
                    "label": "Note",
                    "default": "Changes here will only affect other\nmenus after restarting Avogadro!",
                    "order": 10.0
                }
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
                Path.mkdir(calc_dir, parents=True, exist_ok=True)
            except PermissionError:
                result = {"message": "A folder could not be created at the path specified!"}
                # Pass back to Avogadro to display to user
                print(json.dumps(result))
            config["calc_dir"] = str(calc_dir)
        
        # Save change to xtb_bin if there has been one
        if avo_input["xtb_bin"] != str(xtb_bin):
            xtb_bin = Path(avo_input["xtb_bin"])
            config["xtb_bin"] = str(xtb_bin)
        
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
            json.dump(config, config_path)