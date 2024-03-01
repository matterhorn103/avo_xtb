# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of avo_xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

import argparse
import json
import webbrowser

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
        print("xtb Help")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){10}")

    if args.run_command:
        webbrowser.open("https://xtb-docs.readthedocs.io/en/latest/commandline.html")
        result = {
            "message": "The xtb documentation should have opened in your browser."
        }
        # Pass back to Avogadro
        print(json.dumps(result))
