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
import json
import os
import subprocess
import sys
from pathlib import Path


def find_openbabel():
    # Current directory upon execution of script seems to be the avo "prefix" directory
    prefix_dir = Path.cwd()
    # openbabel should be in the bin directory
    if (prefix_dir / "bin" / "obabel").exists():
        obabel_path = prefix_dir / "bin" / "obabel"
    else:
        obabel_path = "obabel"
    return obabel_path

obabel_path = find_openbabel()

####################################################################################################
# For now all the conversion functions are separate to allow for flexibility
# Obviously it would be possible to combine many into a single function with more arguments

# Turbomole coord >>> xyz
# Maybe at some point do this natively but for now seems easier to use openbabel
# Produced as xtb geometry output if input was also an xyz file
def coord_to_xyz(coord_file):
    # Change working dir to that of file to run openbabel correctly
    os.chdir(coord_file.parent)
    xyz_file = coord_file.with_suffix(".xyz")
    command = [obabel_path, "-i", "tmol", coord_file, "-o", "xyz", "-O", xyz_file]
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")
    return xyz_file


# xyz >>> cjson
def xyz_to_cjson(xyz_file):
    # Change working dir to that of file to run openbabel correctly
    os.chdir(xyz_file.parent)
    cjson_file = xyz_file.with_suffix(".cjson")
    command = [obabel_path, "-i", "xyz", xyz_file, "-o", "cjson", "-O", cjson_file]
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")
    return cjson_file


# Turbomole coord >>> cjson
# Produced as xtb geometry output if input was also a coord file
def coord_to_cjson(coord_file):
    # Change working dir to that if file to run openbabel correctly
    os.chdir(coord_file.parent)
    cjson_file = coord_file.with_suffix(".cjson")
    command = [obabel_path, "-i", "tmol", coord_file, "-o", "cjson", "-O", cjson_file]
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")
    return cjson_file


# Gaussian 98 format >>> cjson
# Frequency calculations with xtb produce "g98.out" files
def g98_to_cjson(g98_file):
    # Change working dir to that of file to run openbabel correctly
    os.chdir(g98_file.parent)
    cjson_file = g98_file.with_suffix(".cjson")
    command = [obabel_path, "-i", "g98", g98_file, "-o", "cjson", "-O", cjson_file]
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")
    return cjson_file


