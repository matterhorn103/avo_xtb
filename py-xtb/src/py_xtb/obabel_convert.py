# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of py-xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

"""Converts files to another format using an Open Babel binary."""

import os
import subprocess
from pathlib import Path

from config import obabel_bin

# Most commands rely on the functionality in this module
# This thus effectively disables the menu command if executing would be impossible
if obabel_bin is None:
    raise FileNotFoundError("Open Babel binary not found.")
    quit()

# For now all the conversion functions are separate to allow for flexibility
# Obviously it would be possible to combine many into a single function with more arguments
# Maybe at some point do these natively but for now seems easier to use openbabel


# tmol is produced as xtb geometry output if input was also a tmol file
def tmol_to_xyz(tmol_file: Path) -> Path:
    """Convert a (tmol/coord) Turbomole format geometry file to xyz format using Open Babel."""
    # Change working dir to that of file to run openbabel correctly
    os.chdir(tmol_file.parent)
    xyz_file = tmol_file.with_suffix(".xyz")
    command = [obabel_bin, "-i", "tmol", tmol_file, "-o", "xyz", "-O", xyz_file]
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")  # noqa: F841
    return xyz_file


def xyz_to_cjson(xyz_file: Path) -> Path:
    """Convert an xyz format geometry file to cjson format using Open Babel."""
    # Change working dir to that of file to run openbabel correctly
    os.chdir(xyz_file.parent)
    cjson_file = xyz_file.with_suffix(".cjson")
    command = [obabel_bin, "-i", "xyz", xyz_file, "-o", "cjson", "-O", cjson_file]
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")  # noqa: F841
    return cjson_file


def tmol_to_cjson(tmol_file: Path) -> Path:
    """Convert a (tmol/coord) Turbomole format geometry file to cjson format using Open Babel."""
    # Change working dir to that of file to run openbabel correctly
    os.chdir(tmol_file.parent)
    cjson_file = tmol_file.with_suffix(".cjson")
    command = [obabel_bin, "-i", "tmol", tmol_file, "-o", "cjson", "-O", cjson_file]
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")  # noqa: F841
    return cjson_file


# Frequency calculations with xtb produce "g98.out" files
def g98_to_cjson(g98_file: Path) -> Path:
    """Convert a Gaussian 98 format output file to cjson format using Open Babel"""
    # Change working dir to that of file to run openbabel correctly
    os.chdir(g98_file.parent)
    cjson_file = g98_file.with_suffix(".cjson")
    command = [obabel_bin, "-i", "g98", g98_file, "-o", "cjson", "-O", cjson_file]
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")  # noqa: F841
    return cjson_file
