# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""Configure various options via the GUI."""

import argparse
import json
import platform
import shutil
import sys
from pathlib import Path

import easyxtb


# Package root is two levels up from this file (avo_xtb/config.py -> avo_xtb/ -> pkg_root)
_pkg_root = Path(__file__).parent.parent


def _pixi_bin_path(name: str) -> Path | None:
    """Return the expected pixi environment binary path for the given program name,
    or None if it doesn't exist."""
    if platform.system() == "Windows":
        candidate = _pkg_root / ".pixi" / "envs" / "default" / "Library" / "bin" / f"{name}.exe"
    else:
        candidate = _pkg_root / ".pixi" / "envs" / "default" / "bin" / name
    return candidate if candidate.exists() else None


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

_options_file = Path(__file__).parent / "options" / "config-options.json"


def get_config_options() -> dict:
    with open(_options_file) as f:
        inner = json.load(f)
    options = {"userOptions": inner}

    # Populate with current runtime values; fall back to PATH then pixi env path
    def _resolve_bin(name: str, configured_path) -> Path | None:
        if configured_path:
            return configured_path
        in_path = shutil.which(name)
        if in_path:
            return Path(in_path)
        return _pixi_bin_path(name)

    xtb_path = _resolve_bin("xtb", easyxtb.XTB.path)
    crest_path = _resolve_bin("crest", easyxtb.CREST.path)
    options["userOptions"]["xtb_bin"]["default"] = str(xtb_path) if xtb_path else ""
    options["userOptions"]["crest_bin"]["default"] = str(crest_path) if crest_path else ""
    options["userOptions"]["user_dir"]["default"] = str(easyxtb.CALCS_DIR)

    for option in ["n_proc", "energy_units", "solvent", "opt_lvl"]:
        if easyxtb.config.get(option) is not None:
            options["userOptions"][option]["default"] = easyxtb.config[option]

    if easyxtb.config.get("method") is not None:
        options["userOptions"]["method"]["default"] = methods[easyxtb.config["method"]]

    for option in ["xtb_opts", "crest_opts"]:
        if easyxtb.config.get(option) is not None:
            opts_dict = easyxtb.config[option]
            opts_string = convert_options(opts_dict=opts_dict)[0]
            options["userOptions"][option]["default"] = opts_string

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
        update_config(avo_input)
