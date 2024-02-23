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

from config import obabel_bin


# Most commands rely on the functionality in this module
# This thus effectively disables the menu command if executing would be impossible
if obabel_bin is None:
    raise FileNotFoundError("Open Babel binary not found.")
    quit()

####################################################################################################
# CONVERSIONS USING OPEN BABEL
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
    # Change working dir to that if file to run openbabel correctly
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

####################################################################################################
# INTERNAL CONVERSIONS (NO OPEN BABEL)

# Convert an energy in the specified unit to a dictionary of all useful units
def convert_energy(energy: float, unit: str) -> dict:
    """Return a dictionary of equivalent energies in different units."""
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


def xyz_from_cjson(
        cjson: dict,
        coords: bool = False
        ) -> list | tuple[int, list[list[str]]]:
    """ Take cjson dict and return geometry in xyz format.

    If `coords=False`, the geometry is returned as a list of lines of an xyz file.
    If `coords=True`, a tuple is returned of the number of atoms, and the
    coordinates as a list of lists.
    """
    all_coords = cjson["atoms"]["coords"]["3d"]
    all_element_numbers = cjson["atoms"]["elements"]["number"]
    # Format into list of lists in style of xyz file i.e. [[El,x,y,z],[El,x,y,z],...]
    n_atoms = len(all_element_numbers)
    coords_array = []
    for index, element in enumerate(all_element_numbers):
        atom = [get_element_symbol(element), str(all_coords[index * 3]), str(all_coords[(index * 3) + 1]), str(all_coords[(index * 3) + 2])]
        coords_array.append(atom)
    if coords:
        return n_atoms, coords_array
    else:
        xyz = [n_atoms, "xyz converted from cjson by avo_xtb"]
        for atom in coords_array:
            # Turn each atom (line of array) into a single string and add to xyz
            atom_line = "     ".join(atom)
            # Make everything line up by removing a space in front of each minus
            atom_line.replace(" -", "-")
            xyz.append(atom_line)
        return xyz


def get_element_symbol(num: int) -> str:
    """Return the element symbol for the provided atomic number."""
    element_dict = {
        1: "H",
        2: "He",
        3: "Li",
        4: "Be",
        5: "B",
        6: "C",
        7: "N",
        8: "O",
        9: "F",
        10: "Ne",
        11: "Na",
        12: "Mg",
        13: "Al",
        14: "Si",
        15: "P",
        16: "S",
        17: "Cl",
        18: "Ar",
        19: "K",
        20: "Ca",
        21: "Sc",
        22: "Ti",
        23: "V",
        24: "Cr",
        25: "Mn",
        26: "Fe",
        27: "Co",
        28: "Ni",
        29: "Cu",
        30: "Zn",
        31: "Ga",
        32: "Ge",
        33: "As",
        34: "Se",
        35: "Br",
        36: "Kr",
        37: "Rb",
        38: "Sr",
        39: "Y",
        40: "Zr",
        41: "Nb",
        42: "Mo",
        43: "Tc",
        44: "Ru",
        45: "Rh",
        46: "Pd",
        47: "Ag",
        48: "Cd",
        49: "In",
        50: "Sn",
        51: "Sb",
        52: "Te",
        53: "I",
        54: "Xe",
        55: "Cs",
        56: "Ba",
        57: "La",
        58: "Ce",
        59: "Pr",
        60: "Nd",
        61: "Pm",
        62: "Sm",
        63: "Eu",
        64: "Gd",
        65: "Tb",
        66: "Dy",
        67: "Ho",
        68: "Er",
        69: "Tm",
        70: "Yb",
        71: "Lu",
        72: "Hf",
        73: "Ta",
        74: "W",
        75: "Re",
        76: "Os",
        77: "Ir",
        78: "Pt",
        79: "Au",
        80: "Hg",
        81: "Tl",
        82: "Pb",
        83: "Bi",
        84: "Po",
        85: "At",
        86: "Rn",
    }
    return element_dict[num]