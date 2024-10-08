# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of avo_xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

"""Automatically download xtb and crest binaries from their repositories on behalf of the user."""

import argparse
import json
import os
import platform
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

from support import py_xtb


# For now just hard code the URLs of xtb and crest
if platform.system() == "Windows":
    xtb_url = "https://github.com/grimme-lab/xtb/releases/download/v6.7.1/xtb-6.7.1pre-Windows-x86_64.zip"
    crest_url = "Not available for Windows!"
elif platform.system() == "Darwin":
    xtb_url = "Not available for macOS!"
    crest_url = "Not available for macOS!"
elif platform.system() == "Linux":
    xtb_url = "https://github.com/grimme-lab/xtb/releases/download/v6.7.1/xtb-6.7.1-linux-x86_64.tar.xz"
    crest_url = "https://github.com/crest-lab/crest/releases/download/v3.0.2/crest-gnu-12-ubuntu-latest.tar.xz"


def download(url, parent_dir) -> Path:
    archive_name = url.split("/")[-1]
    archive_path = parent_dir / archive_name
    urllib.request.urlretrieve(url, archive_path)
    return archive_path


def extract_zip(archive, target_dir) -> Path:
    with zipfile.ZipFile(archive, "r") as zip:
        # Get name of file or folder that will be placed into target
        extracted = target_dir / zip.namelist()[0].split(os.sep)[0]
        zip.extractall(target_dir)
    return extracted


def extract_tar(archive, target_dir) -> Path:
    with tarfile.open(archive, "r:xz") as tar:
        # Get name of file or folder that will be placed into target
        extracted = target_dir / tar.getnames()[0].split(os.sep)[0]
        tar.extractall(target_dir)
    return extracted


def get_xtb(url, install_dir):
    # Download archive to specified directory, then extract there
    archive = download(url, install_dir)
    if archive.suffix == ".zip":
        xtb_folder = extract_zip(archive, install_dir)
    else:
        xtb_folder = extract_tar(archive, install_dir)
    # Rename unzipped folder to non-versioned so that config.py finds it
    xtb_folder.rename(xtb_folder.with_name("xtb"))
    # Remove archive
    archive.unlink()


def get_crest(url, install_dir):
    # Don't install crest if url not valid
    if url[0:5] != "https":
        return
    else:
        archive = download(url, install_dir)
        if archive.suffix == ".zip":
            extract_zip(archive, install_dir)
        else:
            extract_tar(archive, install_dir)
        # Remove archive
        archive.unlink()


def link_xtb_bin(install_dir):
    # xtb binary will be in nested folder, we want it at top level as link
    bin_path = Path(install_dir / "xtb-dist" / "bin" / "xtb")
    # Check Windows
    if bin_path.with_suffix(".exe").exists():
        bin_path = bin_path.with_suffix(".exe")
    # Link
    py_xtb.XTB_BIN = py_xtb.BIN_DIR / bin_path.name
    py_xtb.XTB_BIN.symlink_to(bin_path)
    # Add to config
    py_xtb.config["xtb_bin"] = str(py_xtb.XTB_BIN)
    # Save config
    py_xtb.conf.save_config()


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
    if py_xtb.xtb_bin is not None:
        quit()

    if args.print_options:
        options = {
            "userOptions": {
                "info": {
                    "type": "text",
                    "label": "Info",
                    "default": "xtb was not found on launch!\nThis tool can install it for you.",
                    "order": 1.0,
                },
                "xtb_url": {
                    "type": "text",
                    "label": "xtb URL",
                    "default": xtb_url,
                    "order": 2.0,
                },
                "crest_url": {
                    "type": "text",
                    "label": "crest URL",
                    "default": crest_url,
                    "order": 3.0,
                },
                "install_dir": {
                    "type": "string",
                    "label": "Install in",
                    "default": str(py_xtb.conf.BIN_DIR),
                    "order": 5.0,
                },
                "notice": {
                    "type": "text",
                    "label": "By clicking OK",
                    "default": "xtb and crest will be installed from the Grimme group repositories to the above location.",
                    "order": 6.0,
                },
                "license": {
                    "type": "text",
                    "label": "Important",
                    "default": "xtb and crest are distributed independently under the LGPL license v3.\nThe authors of Avogadro and avo_xtb bear no responsibility for xtb or crest or the contents of the Grimme group's repositories.\nSource code for the programs is available at the above web addresses.",
                    "order": 7.0,
                },
            }
        }
        print(json.dumps(options))
    if args.display_name:
        print("Get xtb…")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){30}")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())

        install_dir = Path(avo_input["install_dir"])

        if platform.system() == "Darwin":
            result = {
                "message": "The Grimme group does not supply binaries for macOS.\nYou will have to install xtb manually.\nSorry!"
            }

        else:
            # First make sure the install directory exists
            try:
                install_dir.mkdir(parents=True, exist_ok=True)
                # Check write permissions
                (install_dir / "probe_file.txt").touch()
                (install_dir / "probe_file.txt").unlink()
            except PermissionError:
                result = {"message": "Install directory is not writeable"}
            else:
                get_xtb(xtb_url, install_dir)
                get_crest(crest_url, install_dir)
                link_xtb_bin(install_dir)
                # Report success
                result = {
                    "message": "xtb (and crest if requested) were successfully installed.\nPlease restart Avogadro."
                }

        # Pass result back to Avogadro to display to user
        print(json.dumps(result))
