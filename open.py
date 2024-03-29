# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of avo_xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

"""Provide a link to the location in the file system of the most recent calculation."""

import argparse
import json
import platform
import subprocess

from config import calc_dir


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
        options = {}
        print(json.dumps(options))
    if args.display_name:
        print("Go to Calculation Files")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){340}")

    if args.run_command:
        # Have to detect os
        if platform.system() == "Windows":
            subprocess.run(["start", calc_dir])

        elif platform.system() == "Darwin":
            subprocess.run(["open", calc_dir])

        else:
            subprocess.run(["xdg-open", calc_dir])
