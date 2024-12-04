# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import json
import logging
import re
import subprocess
import sys

from support import easyxtb


logger = logging.getLogger(__name__)


# Get xtb and crest versions
# Regex to match version numbers (e.g., 6.7.1, 2.12, 6.4.0)
pattern = r"\bversion\s+(\d+\.\d+\.\d+|\d+\.\d+)\b"

if easyxtb.XTB_BIN:
    xtb_version_info = subprocess.run(
        [str(easyxtb.XTB_BIN), "--version"],
        encoding="utf-8",
        capture_output=True,
    ).stdout
    XTB_VERSION = re.findall(pattern, xtb_version_info, re.IGNORECASE)[0]
else:
    XTB_VERSION = None
if easyxtb.CREST_BIN:
    crest_version_info = subprocess.run(
        [str(easyxtb.CREST_BIN), "--version"],
        encoding="utf-8",
        capture_output=True,
    ).stdout
    CREST_VERSION = re.findall(pattern, crest_version_info, re.IGNORECASE)[0]
else:
    CREST_VERSION = None


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
        output = avo_input.copy()

        if XTB_VERSION:
            xtb_version_msg = XTB_VERSION
        else:
            xtb_version_msg = "No xtb binary found"
        if CREST_VERSION:
            crest_version_msg = CREST_VERSION
        else:
            crest_version_msg = "No CREST binary found"

        # Do nothing to data other than add message with version and path info
        output["message"] = (
            "avo_xtb plugin\n"
            + f"easyxtb version: {easyxtb.configuration.easyxtb_VERSION}\n"
            + f"xtb version: {xtb_version_msg}\n"
            + f"xtb path: {easyxtb.XTB_BIN}\n"
            + f"CREST version: {crest_version_msg}\n"
            + f"CREST path: {easyxtb.CREST_BIN}"
        )
        
        # Pass back to Avogadro
        print(json.dumps(output))
        logger.debug(f"The following dictionary was passed back to Avogadro: {output}")
