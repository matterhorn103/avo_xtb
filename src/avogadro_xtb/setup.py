# SPDX-FileCopyrightText: 2026 Matthew Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""One-time setup."""

import hashlib
import os
from pathlib import Path
import shutil
import urllib.request

XTB_BIN_URL_WINDOWS = "https://github.com/grimme-lab/xtb/releases/download/v6.7.1/xtb-6.7.1pre-windows-x86_64.zip"
XTB_HASH_WINDOWS = "043e578da4a7e114a4d584972959a875e3ffb9f2767a86723b95aa6719d28d9c"

# The path to the xtb binary within the extracted folder
XTB_TREE_PATH_WINDOWS = "xtb-6.7.1/bin/xtb.exe"

PIXI_PROJECT_ROOT = os.environ.get("PIXI_PROJECT_ROOT")

def win():
    """Set up things appropriately on Windows by installing an xtb binary from GitHub."""

    # Only need to do this for Pixi installs, as otherwise the user is responsible for sourcing xtb
    # themselves
    if PIXI_PROJECT_ROOT is None:
        print("Not a pixi project")
        return
    
    archive, message = urllib.request.urlretrieve(XTB_BIN_URL_WINDOWS)
    with open(archive, "rb") as f:
        contents = f.read()
        hash = hashlib.sha256()
        hash.update(contents)
        print(hash.hexdigest())
        print(XTB_HASH_WINDOWS)
        success = hash.hexdigest() == XTB_HASH_WINDOWS
        print(success)
    
    pixi_root = Path(PIXI_PROJECT_ROOT)
    bin_dir = pixi_root / ".pixi/envs/default/bin"
    shutil.unpack_archive(archive, bin_dir, "zip")
    # Create a symlink to the actual binary
    (bin_dir / "xtb.exe").symlink_to(bin_dir / XTB_TREE_PATH_WINDOWS)
    

def setup():
    """Run setup, which should only happen on Windows."""
    win()
