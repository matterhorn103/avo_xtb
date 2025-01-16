# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""Configure various options via the GUI."""

import argparse
import json
import sys
from pathlib import Path

from support import easyxtb


def convert_options(
    opts_string: str | None = None,
    opts_dict: dict | None = None,
) -> tuple[str, dict]:
    """Convert a series of command line options passed as a semicolon-delimited string
    to a dict and vice versa."""
    if opts_string is None and opts_dict is None:
        raise ValueError("Must provide either string or dict")
    elif opts_string is None:
        opts_string = ""
        for opt, arg in opts_dict.items():
            if len(opt) == 1:
                opts_string += f" -{opt}"
            else:
                opts_string += f" --{opt}"
            if arg is True:
                opts_string += ";"
            else:
                opts_string += f" {arg};"
        opts_string = opts_string.lstrip().rstrip(";")
    elif opts_dict is None:
        opts_dict = {}
        opts_split = [x.strip() for x in opts_string.split(";")]
        for opt_arg in opts_split:
            if opt_arg == "":
                continue
            opt_arg_split = opt_arg.split(" ", maxsplit=1)
            opt = opt_arg_split[0].lstrip("-")
            try:
                arg = opt_arg_split[1]
            except IndexError:
                arg = True
            opts_dict[opt] = arg
    return opts_string, opts_dict


# List of available methods
methods = ["GFN0-xTB", "GFN1-xTB", "GFN2-xTB"]


def get_config_options() -> dict:
    options = {
        "userOptions": {
            "xtb_bin": {
                "type": "filePath",
                "label": "Location of the xtb binary",
                "default": str(easyxtb.XTB.path),
                "order": 1.0,
            },
            "crest_bin": {
                "type": "filePath",
                "label": "Location of the CREST binary",
                "default": str(easyxtb.CREST.path),
                "order": 2.0,
            },
            "user_dir": {
                "type": "string",
                "label": "Run calculations in",
                "default": str(easyxtb.CALCS_DIR),
                "order": 3.0,
            },
            "n_proc": {
                "type": "integer",
                "label": "Parallel processes to run",
                "minimum": 1,
                "default": 1,
                "order": 4.0
                },
            "energy_units": {
                "type": "stringList",
                "label": "Preferred energy units",
                "values": ["kJ/mol", "kcal/mol"],
                "default": 0,
                "order": 5.0,
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
                "order": 6.0,
            },
            "method": {
                "type": "stringList",
                "label": "Method",
                "values": methods,
                "default": methods[-1],
                "order": 7.0,
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
                "order": 8.0,
            },
            "xtb_opts": {
                "type": "string",
                "label": "Extra command line options for xtb (separate with ;)",
                "default": "",
                "order": 9.0,
            },
            "crest_opts": {
                "type": "string",
                "label": "Extra command line options for CREST (separate with ;)",
                "default": "",
                "order": 10.0,
            },
            "warning": {
                "type": "text",
                "label": "Note",
                "default": "Some changes here will only affect other\ndialogs after restarting Avogadro!",
                "order": 12.0,
            },
        }
    }
    # Populate with any values found in user config
    for option in options["userOptions"].keys():
        if easyxtb.config.get(option) is not None:
            if option in ["xtb_opts", "crest_opts"]:
                opts_dict = easyxtb.config[option]
                opts_string = convert_options(opts_dict=opts_dict)[0]
                options["userOptions"][option]["default"] = opts_string
            else:
                options["userOptions"][option]["default"] = easyxtb.config[option]
    return options


def update_config(avo_input: dict):
    # Replace any string none with actual Python None
    for k, v in avo_input.items():
        if v == "none" or v == "None":
            avo_input[k] = None

    # Save change to user_dir if there has been one
    if avo_input["user_dir"] != str(easyxtb.CALCS_DIR):
        easyxtb.CALCS_DIR = Path(avo_input["user_dir"])
        easyxtb.TEMP_DIR = easyxtb.CALCS_DIR / "last"
        try:
            easyxtb.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            output = {
                "message": "A folder could not be created at the path specified!"
            }
            # Pass back to Avogadro to display to user
            print(json.dumps(output))
        easyxtb.config["calcs_dir"] = str(easyxtb.CALCS_DIR.as_posix())

    # Save any changes to binary paths
    for program in ["xtb", "crest"]:
        if not avo_input[f"{program}_bin"]:
            pass
        elif avo_input[f"{program}_bin"] != str():
            bin_path = Path(avo_input[f"{program}_bin"])
            if program == "crest":
                easyxtb.CREST.path = bin_path
            else:
                easyxtb.XTB.path = bin_path
            easyxtb.config[f"{program}_bin"] = str(bin_path.as_posix())

    # Update other options that don't need coercing
    for option in ["n_proc", "energy_units", "solvent", "opt_lvl"]:
        easyxtb.config[option] = avo_input[option]

    # Update method
    easyxtb.config["method"] = methods.index(avo_input["method"])

    # Update extra options for xtb and crest
    xtb_opts_string = convert_options(opts_string=avo_input["xtb_opts"])[1]
    crest_opts_string = convert_options(opts_string=avo_input["crest_opts"])[1]
    easyxtb.config["xtb_opts"] = xtb_opts_string
    easyxtb.config["crest_opts"] = crest_opts_string

    easyxtb.configuration.save_config()


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
        options = get_config_options()
        print(json.dumps(options))
    
    if args.display_name:
        print("Configure…")
    
    if args.menu_path:
        print("Extensions|Semi-Empirical QM (xTB){20}")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        update_config()
