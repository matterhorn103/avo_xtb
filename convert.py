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
import sys
from pathlib import Path

from config import obabel_bin

####################################################################################################
# CONVERSIONS USING OPEN BABEL
# For now all the conversion functions are separate to allow for flexibility
# Obviously it would be possible to combine many into a single function with more arguments

# Turbomole coord >>> xyz
# Maybe at some point do this natively but for now seems easier to use openbabel
# Produced as xtb geometry output if input was also an xyz file
def tmol_to_xyz(tmol_file):
    # Change working dir to that of file to run openbabel correctly
    os.chdir(tmol_file.parent)
    xyz_file = tmol_file.with_suffix(".xyz")
    command = [obabel_bin, "-i", "tmol", tmol_file, "-o", "xyz", "-O", xyz_file]
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")
    return xyz_file


# xyz >>> cjson
def xyz_to_cjson(xyz_file):
    # Change working dir to that of file to run openbabel correctly
    os.chdir(xyz_file.parent)
    cjson_file = xyz_file.with_suffix(".cjson")
    command = [obabel_bin, "-i", "xyz", xyz_file, "-o", "cjson", "-O", cjson_file]
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")
    return cjson_file


# Turbomole tmol >>> cjson
# Produced as xtb geometry output if input was also a tmol file
def tmol_to_cjson(tmol_file):
    # Change working dir to that if file to run openbabel correctly
    os.chdir(tmol_file.parent)
    cjson_file = tmol_file.with_suffix(".cjson")
    command = [obabel_bin, "-i", "tmol", tmol_file, "-o", "cjson", "-O", cjson_file]
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")
    return cjson_file


# Gaussian 98 format >>> cjson
# Frequency calculations with xtb produce "g98.out" files
def g98_to_cjson(g98_file):
    # Change working dir to that of file to run openbabel correctly
    os.chdir(g98_file.parent)
    cjson_file = g98_file.with_suffix(".cjson")
    command = [obabel_bin, "-i", "g98", g98_file, "-o", "cjson", "-O", cjson_file]
    conversion = subprocess.run(command, capture_output=True, encoding="utf-8")
    return cjson_file

####################################################################################################
# INTERNAL CONVERSIONS (NO OPEN BABEL)

# Convert an energy in the specified unit to a dictionary of all useful units
def convert_energy(energy, unit):
    # Whichever unit was passed, convert to hartree
    if unit == "hartree":
        E_hartree = energy
    elif unit == "eV":
        E_hartree = energy / 27.211386245
    elif unit == "kJ":
        E_hartree = energy / 2625.4996395
    elif unit == "kcal":
        E_hartree = energy / 627.50947406
    # Then calculate the others based on that
    E_eV = E_hartree * 27.211386245
    E_kJ = E_hartree * 2625.4996395
    E_kcal = E_hartree * 627.50947406
    E_dict = {"hartree": E_hartree, "eV": E_eV, "kJ": E_kJ, "kcal": E_kcal}
    return E_dict


# Can imagine it will one day be useful to do similar to above but with frequency units
def convert_freq(freq=None, wavelength=None, wavenumber=None):
    return