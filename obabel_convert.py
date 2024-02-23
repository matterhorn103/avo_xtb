"""
Converts files to another format using an Open Babel binary.
"""
"""
avo_xtb
A full-featured interface to xtb in Avogadro 2.
Copyright (c) 2023, Matthew J. Milner

BSD 3-Clause License

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import os
import subprocess
from pathlib import Path
from time import sleep

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
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")
    return xyz_file


def xyz_to_cjson(xyz_file: Path) -> Path:
    """Convert an xyz format geometry file to cjson format using Open Babel."""
    # Change working dir to that of file to run openbabel correctly
    os.chdir(xyz_file.parent)
    cjson_file = xyz_file.with_suffix(".cjson")
    command = [obabel_bin, "-i", "xyz", xyz_file, "-o", "cjson", "-O", cjson_file]
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")
    return cjson_file


def tmol_to_cjson(tmol_file: Path) -> Path:
    """Convert a (tmol/coord) Turbomole format geometry file to cjson format using Open Babel."""
    # Change working dir to that of file to run openbabel correctly
    os.chdir(tmol_file.parent)
    cjson_file = tmol_file.with_suffix(".cjson")
    command = [obabel_bin, "-i", "tmol", tmol_file, "-o", "cjson", "-O", cjson_file]
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")
    return cjson_file


# Frequency calculations with xtb produce "g98.out" files
def g98_to_cjson(g98_file: Path) -> Path:
    """Convert a Gaussian 98 format output file to cjson format using Open Babel"""
    # Change working dir to that of file to run openbabel correctly
    os.chdir(g98_file.parent)
    cjson_file = g98_file.with_suffix(".cjson")
    command = [obabel_bin, "-i", "g98", g98_file, "-o", "cjson", "-O", cjson_file]
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")
    return cjson_file