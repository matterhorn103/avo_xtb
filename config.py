# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of avo_xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

"""Configure various options via the GUI."""

import argparse
import json
import sys
from pathlib import Path

from py_xtb.config import xtb_bin, obabel_bin, calc_dir, config, config_file


# List of available methods
methods = ["GFN0-xTB", "GFN1-xTB", "GFN2-xTB"]

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
                "user_dir": {
                    "type": "string",
                    "label": "Run calculations (in subfolder) in",
                    "default": str(calc_dir.parent),
                    "order": 3.0,
                },
                "energy_units": {
                    "type": "stringList",
                    "label": "Preferred energy units",
                    "values": ["kJ/mol", "kcal/mol"],
                    "default": 0,
                    "order": 4.0,
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
                "method": {
                    "type": "stringList",
                    "label": "Method (xtb only)",
                    "values": methods,
                    "default": methods[-1],
                    "order": 6.0,
                },
                "opt_lvl": {
                    "type": "stringList",
                    "label": "Optimization level (xtb only)",
                    "values": [
                        "crude",
                        "sloppy",
                        "loose",
                        "lax",
                        "normal",
                        "tight",
                        "vtight",
                        "extreme",
                    ],
                    "default": 4,
                    "order": 7.0,
                },
                "warning": {
                    "type": "text",
                    "label": "Note",
                    "default": "Some changes here will only affect other\nmenus after restarting Avogadro!",
                    "order": 10.0,
                },
            }
        }
        # Set other options' defaults to match that found in user config
        for option in ["solvent", "energy_units", "method", "opt_lvl"]:
            if config[option] is not None:
                options["userOptions"][option]["default"] = config[option]
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

        # Update energy units
        config["energy_units"] = avo_input["energy_units"]

        # Convert "none" string to Python None
        if avo_input["solvent"] == "none":
            solvent_selected = None
        else:
            solvent_selected = avo_input["solvent"]

        # Update solvent
        config["solvent"] = solvent_selected

        # Update method
        config["method"] = methods.index(avo_input["method"])

        # Update optimization level
        config["opt_lvl"] = avo_input["opt_lvl"]

        with open(config_file, "w", encoding="utf-8") as config_path:
            json.dump(config, config_path, indent=2)
