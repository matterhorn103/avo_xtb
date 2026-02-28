# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""Automatically download xtb binaries from their repositories on behalf of the user."""

import argparse
import json
import logging
import os
import platform
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

import easyxtb


logger = logging.getLogger(__name__)


# For now just hard code the URLs of xtb
xtb_urls = {
    "Windows": "https://github.com/grimme-lab/xtb/releases/download/v6.7.1/xtb-6.7.1pre-Windows-x86_64.zip",
    "Darwin": None,
    "Linux": "https://github.com/grimme-lab/xtb/releases/download/v6.7.1/xtb-6.7.1-linux-x86_64.tar.xz",
}
crest_urls = {
    "Windows": None,
    "Darwin": None,
    "Linux": "https://github.com/crest-lab/crest/releases/download/v3.0.2/crest-gnu-12-ubuntu-latest.tar.xz",
}


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


_options_file = Path(__file__).parent / "options" / "install-xtb-options.json"


def get_options() -> dict:
    with open(_options_file) as f:
        inner = json.load(f)
    options = {"userOptions": inner}
    options["userOptions"]["xtb_url"]["default"] = xtb_urls[platform.system()]
    options["userOptions"]["install_dir"]["default"] = str(easyxtb.configuration.BIN_DIR)
    return options


def install_xtb(avo_input: dict) -> dict:
    install_dir = Path(avo_input["install_dir"])

    if platform.system() == "Darwin":
        return {
            "message": "The Grimme group does not supply binaries for macOS.\nYou will have to install xtb manually.\nSorry!"
        }

    # First make sure the install directory exists
    try:
        install_dir.mkdir(parents=True, exist_ok=True)
        # Check write permissions
        (install_dir / "probe_file.txt").touch()
        (install_dir / "probe_file.txt").unlink()
    except PermissionError:
        return {"message": "Install directory is not writeable"}

    xtb_bin = get_bin(xtb_urls[platform.system()], install_dir)
    return {
        "message": f"xtb was successfully installed to\n{xtb_bin}\nPlease restart Avogadro."
    }


def get_bin(url: str, install_dir: Path) -> Path:
    # Don't install if url not valid
    if url[0:5] != "https":
        return
    # Download archive to specified directory, then extract there
    archive = download(url, install_dir)
    if archive.suffix == ".zip":
        folder = extract_zip(archive, install_dir)
    else:
        folder = extract_tar(archive, install_dir)
    # Remove archive
    archive.unlink()
    # Rename unzipped folder to a non-versioned name we have chosen
    # Store appropriate path to binary
    if "crest" in folder.name:
        folder = folder.rename(folder.with_name("crest"))
        bin_name = "crest.exe" if platform.system() == "Windows" else "crest"
        bin_path = folder/bin_name
    else:
        folder = folder.rename(folder.with_name("xtb-dist"))
        bin_name = "xtb.exe" if platform.system() == "Windows" else "xtb"
        bin_path = folder/f"bin/{bin_name}"  
    return bin_path


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
    if easyxtb.XTB.path is not None:
        quit()

    if args.print_options:
        print(json.dumps(get_options()))

    if args.display_name:
        print("Get xtb…")

    if args.menu_path:
        print("Extensions|Semi-Empirical QM (xTB){801}")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        output = install_xtb(avo_input)
        # Pass result back to Avogadro to display to user
        print(json.dumps(output))
        logger.debug(f"The following dictionary was passed back to Avogadro: {output}")
