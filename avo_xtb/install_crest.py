# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""Automatically download xtb and crest binaries from their repositories on behalf of the user."""

import argparse
import json
import logging
import platform
import sys
from pathlib import Path

from support import easyxtb
from install_xtb import get_bin, link_bin


logger = logging.getLogger(__name__)


# For now just hard code the URLs for CREST
crest_urls = {
    "Windows": None,
    "Darwin": None,
    "Linux": "https://github.com/crest-lab/crest/releases/download/v3.0.2/crest-gnu-12-ubuntu-latest.tar.xz",
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--print-options", action="store_true")
    parser.add_argument("--run-command", action="store_true")
    parser.add_argument("--display-name", action="store_true")
    parser.add_argument("--lang", nargs="?", default="en")
    parser.add_argument("--menu-path", action="store_true")
    args = parser.parse_args()

    # Disable this command if xtb has been found
    if easyxtb.CREST_BIN is not None:
        quit()

    if args.print_options:
        options = {
            "userOptions": {
                "info": {
                    "type": "text",
                    "label": "Info",
                    "default": "CREST was not found on launch!\nThis tool can install it for you.",
                    "order": 1.0,
                },
                "crest_url": {
                    "type": "text",
                    "label": "CREST URL",
                    "default": crest_urls[platform.system()],
                    "order": 3.0,
                },
                "install_dir": {
                    "type": "string",
                    "label": "Install in",
                    "default": str(easyxtb.configuration.BIN_DIR),
                    "order": 5.0,
                },
                "notice": {
                    "type": "text",
                    "label": "By clicking OK",
                    "default": "CREST will be installed from the CREST GitHub repository to the above location.",
                    "order": 6.0,
                },
                "license": {
                    "type": "text",
                    "label": "Important",
                    "default": "CREST is distributed independently under the LGPL license v3.\nThe authors of Avogadro and avo_xtb bear no responsibility for CREST or the contents of the project's repositories.\nSource code for the program is available at the above web address.",
                    "order": 7.0,
                },
            }
        }
        print(json.dumps(options))
        
    if args.display_name:
        print("Get CREST…")

    if args.menu_path:
        print("Extensions|Semi-Empirical QM (xTB){701}")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())

        install_dir = Path(avo_input["install_dir"])

        if platform.system() != "Linux":
            output = {
                "message": "CREST is unfortunately available only for Linux.\nSorry!"
            }

        else:
            # First make sure the install directory exists
            try:
                install_dir.mkdir(parents=True, exist_ok=True)
                # Check write permissions
                (install_dir / "probe_file.txt").touch()
                (install_dir / "probe_file.txt").unlink()
            except PermissionError:
                output = {"message": "Install directory is not writeable"}
            else:
                crest_folder = get_bin(crest_urls[platform.system()], install_dir)
                if crest_folder:
                    link_bin(crest_folder/"crest")
                # Report success
                output = {
                    "message": "CREST was successfully installed.\nPlease restart Avogadro."
                }

        # Pass result back to Avogadro to display to user
        print(json.dumps(output))
        logger.debug(f"The following dictionary was passed back to Avogadro: {output}")
