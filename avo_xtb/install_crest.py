# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""Automatically download the CREST binary from its repository on behalf of the user."""

import argparse
import json
import logging
import platform
import sys
from pathlib import Path

import easyxtb
from .install_xtb import get_bin


logger = logging.getLogger(__name__)


# For now just hard code the URLs for CREST
crest_urls = {
    "Windows": None,
    "Darwin": None,
    "Linux": "https://github.com/crest-lab/crest/releases/download/v3.0.2/crest-gnu-12-ubuntu-latest.tar.xz",
}

_options_file = Path(__file__).parent / "options" / "install-crest-options.json"


def get_options() -> dict:
    with open(_options_file) as f:
        inner = json.load(f)
    options = {"userOptions": inner}
    options["userOptions"]["crest_url"]["default"] = crest_urls[platform.system()]
    options["userOptions"]["install_dir"]["default"] = str(easyxtb.configuration.BIN_DIR)
    return options


def install_crest(avo_input: dict) -> dict:
    install_dir = Path(avo_input["install_dir"])

    if platform.system() != "Linux":
        return {"message": "CREST is unfortunately available only for Linux.\nSorry!"}

    # First make sure the install directory exists
    try:
        install_dir.mkdir(parents=True, exist_ok=True)
        # Check write permissions
        (install_dir / "probe_file.txt").touch()
        (install_dir / "probe_file.txt").unlink()
    except PermissionError:
        return {"message": "Install directory is not writeable"}

    crest_bin = get_bin(crest_urls[platform.system()], install_dir)
    return {
        "message": f"CREST was successfully installed to\n{crest_bin}\nPlease restart Avogadro."
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

    # Disable this command if crest has been found
    if easyxtb.CREST.path is not None:
        quit()

    if args.print_options:
        print(json.dumps(get_options()))

    if args.display_name:
        print("Get CREST…")

    if args.menu_path:
        print("Extensions|Semi-Empirical QM (xTB){701}")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        output = install_crest(avo_input)
        # Pass result back to Avogadro to display to user
        print(json.dumps(output))
        logger.debug(f"The following dictionary was passed back to Avogadro: {output}")
