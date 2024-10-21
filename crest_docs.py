# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import json
import logging
import sys
import webbrowser


logger = logging.getLogger(__name__)


crest_docs_url = "https://crest-lab.github.io/crest-docs/"


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
        print("CREST Help")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){700}")

    if args.run_command:
        # Still have to read input from Avogadro and pass cjson back
        # Otherwise molecule disappears
        avo_input = json.loads(sys.stdin.read())
        
        logger.debug(f"Opening the crest docs website at {crest_docs_url}")
        webbrowser.open(crest_docs_url)
        result = {
            "message": "The CREST documentation should have opened in your browser.",
            "moleculeFormat": "cjson",
            "cjson": avo_input["cjson"],
        }
        # Pass back to Avogadro
        print(json.dumps(result))
        logger.debug(f"The following dictionary was passed back to Avogadro: {result}")
