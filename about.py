# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of avo_xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

import argparse
import json
import logging
import subprocess
import sys

from support import py_xtb


logger = logging.getLogger(__name__)


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
        print("About avo_xtb")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){10}")

    if args.run_command:

        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        result = avo_input.copy()

        if py_xtb.XTB_BIN:
            xtb_version = subprocess.run(
                [str(py_xtb.XTB_BIN), "--version"],
                encoding="utf-8",
                capture_output=True,
            ).stdout.splitlines()[-2].strip()
        else:
            xtb_version = "No xtb binary found"
        if py_xtb.CREST_BIN:
            crest_version = subprocess.run(
                [str(py_xtb.CREST_BIN), "--version"],
                encoding="utf-8",
                capture_output=True,
            ).stdout.splitlines()[-4].strip()
        else:
            crest_version = "No CREST binary found"

        # Do nothing to data other than add message with version and path info
        result["message"] = (
            "avo_xtb plugin\n"
            + f"py-xtb version: {py_xtb.conf.PY_XTB_VERSION}\n"
            + f"xtb version: {xtb_version}\n"
            + f"xtb path: {py_xtb.XTB_BIN}\n"
            + f"CREST version: {crest_version}\n"
            + f"CREST path: {py_xtb.CREST_BIN}"
        )
        
        # Pass back to Avogadro
        print(json.dumps(result))
        logger.debug(f"The following dictionary was passed back to Avogadro: {result}")
