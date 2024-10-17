# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of avo_xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

"""Configure various options via the GUI."""

import argparse
import json
import sys
from pathlib import Path

from support import py_xtb


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
                    "default": str(py_xtb.XTB_BIN),
                    "order": 1.0,
                },
                "user_dir": {
                    "type": "string",
                    "label": "Run calculations (in subfolder) in",
                    "default": str(py_xtb.CALC_DIR),
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
            if py_xtb.config[option] is not None:
                options["userOptions"][option]["default"] = py_xtb.config[option]
        print(json.dumps(options))
    if args.display_name:
        print("Configure…")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){20}")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())

        # Save change to user_dir if there has been one
        if avo_input["user_dir"] != str(py_xtb.CALC_DIR):
            py_xtb.CALC_DIR = Path(avo_input["user_dir"])
            py_xtb.conf.TEMP_DIR = py_xtb.CALC_DIR / "last"
            try:
                py_xtb.TEMP_DIR.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                result = {
                    "message": "A folder could not be created at the path specified!"
                }
                # Pass back to Avogadro to display to user
                print(json.dumps(result))
            py_xtb.config["calc_dir"] = str(py_xtb.CALC_DIR)

        # Save change to xtb_bin if there has been one
        if avo_input["xtb_bin"] != str(py_xtb.XTB_BIN):
            py_xtb.XTB_BIN = Path(avo_input["xtb_bin"])
            py_xtb.config["xtb_bin"] = str(py_xtb.XTB_BIN)

        # Update energy units
        py_xtb.config["energy_units"] = avo_input["energy_units"]

        # Convert "none" string to Python None
        if avo_input["solvent"] == "none":
            solvent_selected = None
        else:
            solvent_selected = avo_input["solvent"]

        # Update solvent
        py_xtb.config["solvent"] = solvent_selected

        # Update method
        py_xtb.config["method"] = methods.index(avo_input["method"])

        # Update optimization level
        py_xtb.config["opt_lvl"] = avo_input["opt_lvl"]

        py_xtb.conf.save_config()
