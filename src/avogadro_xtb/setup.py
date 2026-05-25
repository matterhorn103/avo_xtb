# SPDX-FileCopyrightText: 2026 Matthew Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""One-time setup."""

import hashlib
import os
import platform
import shutil
import urllib.request
from pathlib import Path

XTB_BIN_URL_WINDOWS = (
    "https://github.com/grimme-lab/xtb/releases/download/v6.7.1/xtb-6.7.1pre-windows-x86_64.zip"
)
XTB_HASH_WINDOWS = "043e578da4a7e114a4d584972959a875e3ffb9f2767a86723b95aa6719d28d9c"
# The path to the xtb binary within the extracted folder
XTB_TREE_PATH_WINDOWS = "xtb-6.7.1/bin/xtb.exe"

XTB_BIN_URL_LINUX = (
    "https://github.com/grimme-lab/xtb/releases/download/v6.7.1/xtb-6.7.1-linux-x86_64.tar.xz"
)
# Should be this but the checksum file on the releases page seems to be incorrect
# XTB_HASH_LINUX = "79a2a2f50091b3b941e5139c1b38a53203d5d2e9ba496a7ad505d8c31ccd6013"
XTB_HASH_LINUX = "62a8d18778286e815292ee53d76ce447daf460a4dea3782c0f25cbac7019b5df"
XTB_TREE_PATH_LINUX = "xtb-dist/bin/xtb"

PIXI_PROJECT_ROOT = os.environ.get("PIXI_PROJECT_ROOT")


def win():
    """Set up things appropriately on Windows by installing an xtb binary from GitHub."""

    # Only need to do this for Pixi installs, as otherwise the user is responsible for sourcing xtb
    # themselves
    if PIXI_PROJECT_ROOT is None:
        print("Not a pixi project – aborting")
        return

    print(f"Downloading archive from {XTB_BIN_URL_WINDOWS}")
    archive, message = urllib.request.urlretrieve(XTB_BIN_URL_WINDOWS)
    print("Download complete")
    with open(archive, "rb") as f:
        contents = f.read()
        hash = hashlib.sha256()
        hash.update(contents)
        print("SHA256 hash of downloaded archive:", hash.hexdigest())
        print("Expected SHA256 hash:             ", XTB_HASH_WINDOWS)
        success = hash.hexdigest() == XTB_HASH_WINDOWS
        if not success:
            print("Hashes do not match – aborting")
            return

    pixi_root = Path(PIXI_PROJECT_ROOT)
    bin_dir = pixi_root / ".pixi/envs/default/bin"
    print(f"Unpacking archive to {bin_dir}")
    shutil.unpack_archive(archive, bin_dir, "zip")
    # Create a link (not a symlink, as that requires admin privileges) to the actual binary
    bin_path = bin_dir / XTB_TREE_PATH_WINDOWS
    link_path = bin_dir / "xtb.exe"
    (link_path).hardlink_to(bin_path)
    print(f"Created a link at {link_path}")
    print(f"               to {bin_path}")


def linux():
    """Set up things appropriately on Linux by installing an xtb binary from GitHub."""

    # Only need to do this for Pixi installs, as otherwise the user is responsible for sourcing xtb
    # themselves
    if PIXI_PROJECT_ROOT is None:
        print("Not a pixi project – aborting")
        return

    print(f"Downloading archive from {XTB_BIN_URL_LINUX}")
    archive, message = urllib.request.urlretrieve(XTB_BIN_URL_LINUX)
    print("Download complete")
    with open(archive, "rb") as f:
        contents = f.read()
        hash = hashlib.sha256()
        hash.update(contents)
        print("SHA256 hash of downloaded archive:", hash.hexdigest())
        print("Expected SHA256 hash:             ", XTB_HASH_LINUX)
        success = hash.hexdigest() == XTB_HASH_LINUX
        if not success:
            print("Hashes do not match – aborting")
            return

    pixi_root = Path(PIXI_PROJECT_ROOT)
    bin_dir = pixi_root / ".pixi/envs/default/bin"
    print(f"Unpacking archive to {bin_dir}")
    shutil.unpack_archive(archive, bin_dir, "xztar")
    # Create a link
    bin_path = bin_dir / XTB_TREE_PATH_LINUX
    link_path = bin_dir / "xtb"
    (link_path).hardlink_to(bin_path)
    print(f"Created a link at {link_path}")
    print(f"               to {bin_path}")


def setup():
    """Run setup, which should only actually do anything on Windows."""
    if platform.system() == "Windows":
        win()
    else:
        linux()
