# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""Provide a link to the location in the file system of the most recent calculation."""

import argparse
import json
import platform
import subprocess

from support import easyxtb


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
            subprocess.run(["explorer.exe", easyxtb.CALC_DIR])

        elif platform.system() == "Darwin":
            subprocess.run(["open", easyxtb.CALC_DIR])

        else:
            subprocess.run(["xdg-open", easyxtb.CALC_DIR])
