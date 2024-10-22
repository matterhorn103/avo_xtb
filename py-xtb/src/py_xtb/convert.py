# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""Functions for various conversions without relying on external dependencies such as Open Babel."""


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


# Having this as a template is easier than constantly having to make sure that a cjson
# already has the nested structure we need in order to avoid KeyErrors
empty_cjson = {
  "chemicalJson": 1,
  "atoms": {
    "coords": {
      "3d": [],
      "3dSets": [],
    },
    "elements": {
      "number": [],
    },
    "formalCharges": [],
    "layer": [],
  },
  "bonds": {
    "connections": {
      "index": [],
    },
    "order": [],
  },
  "properties": {
    "totalCharge": 0,
    "totalSpinMultiplicity": 1,
    "energies": [],
  },
}


def cjson_to_xyz(
    cjson: dict, lines: bool = False
) -> list[str] | tuple[int, list[list[str]]]:
    """Take cjson dict and return geometry in xyz style.

    If `lines=True`, the geometry is returned as a list of lines of an xyz file.
    If `lines=False`, a tuple is returned of the number of atoms, and the elements
    and coordinates as a list of lists i.e. [[El,x,y,z],[El,x,y,z],...].
    """
    all_coords = cjson["atoms"]["coords"]["3d"]
    all_element_numbers = cjson["atoms"]["elements"]["number"]
    # Format into list of lists in style of xyz file i.e. [[El,x,y,z],[El,x,y,z],...]
    n_atoms = len(all_element_numbers)
    coords_array = []
    for index, element in enumerate(all_element_numbers):
        atom = [
            get_element_symbol(element),
            str(all_coords[index * 3]),
            str(all_coords[(index * 3) + 1]),
            str(all_coords[(index * 3) + 2]),
        ]
        coords_array.append(atom)
    if not lines:
        return n_atoms, coords_array
    else:
        xyz = [str(n_atoms), "xyz converted from cjson by avo_xtb"]
        for atom in coords_array:
            # Turn each atom (line of array) into a single string and add to xyz
            atom_line = "     ".join(atom)
            # Make everything line up by removing a space in front of each minus
            atom_line.replace(" -", "-")
            xyz.append(atom_line)
        return xyz


def xyz_to_cjson(
    xyz_lines: list[str] = None,
    xyz_tuple: tuple[int, list[str]] = None,
) -> dict:
    """Take geometry in xyz style and return cjson dict.

    Provide either a list of the lines of an xyz file, or a tuple of the number of atoms
    and the coordinates as a list of lists of strings i.e. [[El,x,y,z],[El,x,y,z],...]
    Note that coordinates are stored in the cjson dict as floats, not strings.
    """
    # Convert to array of coordinates
    if xyz_lines:
        n_atoms = int(xyz_lines[0])
        coords_array = []
        for atom_line in xyz_lines[2:]:
            atom = atom_line.split()
            if len(atom) > 0:
                coords_array.append(atom)
    elif xyz_tuple:
        n_atoms, coords_array = xyz_tuple
    all_coords = []
    all_element_numbers = []
    for atom in coords_array:
        element = atom[0]
        all_element_numbers.append(get_atomic_number(element))
        all_coords.extend([float(atom[1]), float(atom[2]), float(atom[3])])
    cjson = {"atoms": {"coords": {"3d": all_coords}, "elements": all_element_numbers}}
    return cjson


def freq_to_cjson(frequencies: list[dict]) -> dict:
    """Takes frequency data in the form of a dict of properties per frequency in a list,
    as produced by a `hess` or `ohess` calculation, and returns the results as a CJSON."""

    freq_cjson = {
        "vibrations": {
            "frequencies": [],
            "modes": [],
            "intensities": [],
            "eigenVectors": [],
        }
    }
    
    for f in frequencies:
        freq_cjson["vibrations"]["frequencies"].append(f["frequency"])
        freq_cjson["vibrations"]["modes"].append(f["mode"])
        freq_cjson["vibrations"]["intensities"].append(f["ir_intensity"])
        flattened_eigenvectors = []
        for atom in f["eigenvectors"]:
            flattened_eigenvectors.extend(atom)
        freq_cjson["vibrations"]["eigenVectors"].append(flattened_eigenvectors)
    
    return freq_cjson


def conf_to_cjson(conformers: list[dict]) -> dict:
    """Takes conformer data in the form of a dict of properties per conformer in a list,
    as produced by a calculation with CREST, and returns the results as a CJSON."""

    conf_cjson = {
        "atoms": {
            "coords": {
                "3dSets": [],
            },
        },
        "properties": {
            "energies": [],
        },
    }

    for c in conformers:
        conf_cjson["atoms"]["coords"]["3dSets"].append(
            c["geometry"].to_cjson()["atoms"]["coords"]["3d"]
        )
        conf_cjson["properties"]["energies"].append(c["energy"])
    
    return conf_cjson


def taut_to_cjson(tautomers: list[dict]) -> dict:
    """Takes tautomer data in the form of a dict of properties per tautomer in a list,
    as produced by a calculation with CREST, and returns the results as a CJSON.
    
    Currently works identically to `conf_to_cjson()` under the hood.
    """
    return conf_to_cjson(tautomers)


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


def get_atomic_number(element_symbol: str) -> int:
    """Return the atomic number for the provided element symbol (case insensitive)."""
    element_dict = {
        "H": 1,
        "He": 2,
        "Li": 3,
        "Be": 4,
        "B": 5,
        "C": 6,
        "N": 7,
        "O": 8,
        "F": 9,
        "Ne": 10,
        "Na": 11,
        "Mg": 12,
        "Al": 13,
        "Si": 14,
        "P": 15,
        "S": 16,
        "Cl": 17,
        "Ar": 18,
        "K": 19,
        "Ca": 20,
        "Sc": 21,
        "Ti": 22,
        "V": 23,
        "Cr": 24,
        "Mn": 25,
        "Fe": 26,
        "Co": 27,
        "Ni": 28,
        "Cu": 29,
        "Zn": 30,
        "Ga": 31,
        "Ge": 32,
        "As": 33,
        "Se": 34,
        "Br": 35,
        "Kr": 36,
        "Rb": 37,
        "Sr": 38,
        "Y": 39,
        "Zr": 40,
        "Nb": 41,
        "Mo": 42,
        "Tc": 43,
        "Ru": 44,
        "Rh": 45,
        "Pd": 46,
        "Ag": 47,
        "Cd": 48,
        "In": 49,
        "Sn": 50,
        "Sb": 51,
        "Te": 52,
        "I": 53,
        "Xe": 54,
        "Cs": 55,
        "Ba": 56,
        "La": 57,
        "Ce": 58,
        "Pr": 59,
        "Nd": 60,
        "Pm": 61,
        "Sm": 62,
        "Eu": 63,
        "Gd": 64,
        "Tb": 65,
        "Dy": 66,
        "Ho": 67,
        "Er": 68,
        "Tm": 69,
        "Yb": 70,
        "Lu": 71,
        "Hf": 72,
        "Ta": 73,
        "W": 74,
        "Re": 75,
        "Os": 76,
        "Ir": 77,
        "Pt": 78,
        "Au": 79,
        "Hg": 80,
        "Tl": 81,
        "Pb": 82,
        "Bi": 83,
        "Po": 84,
        "At": 85,
        "Rn": 86,
    }
    # Make sure symbol is capitalized
    return element_dict[element_symbol.title()]
