# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from .convert import get_atomic_number, get_element_symbol
from .format import cjson_dumps


logger = logging.getLogger(__name__)


@dataclass
class Atom:
    """An atom with an element symbol and 3D coordinates in ångstrom."""
    element: str
    x: float
    y: float
    z: float


class Geometry:
    def __init__(
        self,
        atoms: list[Atom],
        charge: int = 0,
        spin: int = 0,
        _comment: str | None = None,
    ):
        """A set of atoms within a 3D space for use in calculations with an associated
        charge and spin.

        Provides class methods for creation from, and instance methods for writing to,
        XYZ and CJSON formats.
        
        The coordinates should be provided as a list of `Atom` objects.

        `spin` is the number of unpaired electrons.
        """
        self.atoms = atoms
        self.charge = charge
        if spin >= 0:
            self.spin = spin
        else:
            raise ValueError("spin (number of unpaired electrons) cannot be negative")
        self._comment = _comment
    
    def __iter__(self):
        """Geometries are iterable over their Atoms."""
        return iter(self.atoms)
    
    def to_xyz(self, comment: str | None = None) -> list[str]:
        "Generate an XYZ, as a list of lines, for the geometry."
        logger.debug("Generating an xyz, as a list of lines, for the geometry")
        if comment is None:
            comment = self._comment if self._comment else "xyz prepared by easyxtb"
        xyz = [str(len(self.atoms)), comment]
        for a in self.atoms:
            # Turn each atom (line of array) into a single string and add to xyz
            # xtb and ORCA use 14 decimal places for XYZs and Avogadro writes between 14
            # and 16 to CJSON so let's match that
            atom_line = "     ".join([
                a.element + (" " * (5 - len(a.element))),
                f"{a.x:.14f}",
                f"{a.y:.14f}",
                f"{a.z:.14f}",
            ])
            # Make everything line up by removing a space in front of each minus
            atom_line = atom_line.replace(" -", "-")
            xyz.append(atom_line)
        return xyz
    
    def to_cjson(self) -> dict:
        """Generate a CJSON, as a Python dict, for the geometry."""
        logger.debug("Generating a cjson, as a Python dict, for the geometry")
        all_coords = []
        all_element_numbers = []
        for atom in self.atoms:
            all_element_numbers.append(get_atomic_number(atom.element))
            all_coords.extend([float(atom.x), float(atom.y), float(atom.z)])
        cjson = {
            "chemicalJson": 1,
            "atoms": {
                "coords": {
                    "3d": all_coords,
                },
                "elements": {
                    "number": all_element_numbers,
                },
            },
            "properties": {
                "totalCharge": self.charge,
                "totalSpinMultiplicity": self.spin + 1,
            }
        }
        return cjson

    def write_xyz(self, dest: os.PathLike) -> os.PathLike:
        """Write geometry to an XYZ file at the provided path.
        
        The file is written with a trailing newline.
        """
        logger.debug(f"Saving the geometry as an xyz file to {dest}")
        # Make sure it ends with a newline
        lines = self.to_xyz() + [""]
        with open(dest, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return dest
    
    def write_cjson(
        self,
        dest: os.PathLike,
        prettyprint=True,
        indent=2,
        **kwargs,
    ) -> os.PathLike:
        """Write geometry to a CJSON file at the provided path.
        
        With the default `prettyprint` option, all simple arrays (not themselves
        containing objects/dicts or arrays/lists) will be flattened onto a single line,
        while all other array elements and object members will be pretty-printed with
        the specified indent level (2 spaces by default).

        `indent` and any `**kwargs` are passed to Python's `json.dumps()` as is, so the
        same values are valid e.g. `indent=0` will insert newlines while `indent=None`
        will afford a compact single-line representation.

        The file is written with a trailing newline.
        """
        logger.debug(f"Saving the geometry as a cjson file to {dest}")
        cjson = self.to_cjson()
        cjson_string = cjson_dumps(cjson, prettyprint=prettyprint, indent=indent, **kwargs)
        # Make sure it ends with a newline
        cjson_string += "\n"
        with open(dest, "w", encoding="utf-8") as f:
            f.write(cjson_string)
        return dest

    def to_file(self, dest: os.PathLike, format: str = None) -> os.PathLike:
        """Write geometry to an XYZ or CJSON file.
        
        The format can be specified by passing either ".xyz" or ".cjson" as the `format`
        argument, or it can be left to automatically be detected based on the filename
        ending.
        """
        filepath = Path(dest)
        # Autodetect format of file
        if format is None:
            format = filepath.suffix
        if format == ".xyz":
            self.write_xyz(dest)
        if format == ".cjson":
            self.write_cjson(dest)
        return dest

    @classmethod
    def from_xyz(cls, xyz_lines: list[str], charge: int = 0, spin: int = 0):
        """Create a `Geometry` object from an XYZ in the form of a list of lines."""
        logger.debug("Instantiating a geometry from an xyz")
        atoms = []
        for atom_line in xyz_lines[2:]:
            atom_parts = atom_line.split()
            # Guard against empty final line or line starting with something other than
            # an element symbol
            if len(atom_parts) >= 4 and atom_parts[0].isalpha():
                coords = [float(n) for n in atom_parts[1:4]]
                atoms.append(
                    Atom(atom_parts[0], *[float(n) for n in atom_parts[1:4]])
                )
        return Geometry(atoms, charge, spin, _comment=xyz_lines[1])
    
    @classmethod
    def from_multi_xyz(cls, xyz_lines: list[str], charge: int = 0, spin: int = 0):
        """Create a set of `Geometry` objects from an XYZ (in the form of a list of
        lines) that contains multiple different structures.
        
        All structures must have the same number of atoms, though the order and elements
        of the atoms must not necessarily be identical.

        The number and content of lines between structures is pretty much irrelevant.
        """
        logger.debug("Instantiating a set of geometries from a multi-structure xyz")
        atom_count_line = xyz_lines[0]
        geometries = []
        current_xyz = []
        for i, l in enumerate(xyz_lines):
            current_xyz.append(l)
            if i == len(xyz_lines) - 1 or xyz_lines[i+1] == atom_count_line:
                geometries.append(cls.from_xyz(current_xyz, charge, spin))
                current_xyz = []
        return geometries
    
    @classmethod
    def from_cjson(cls, cjson_dict: dict, charge: int = None, spin: int = None):
        """Create a `Geometry` object from an CJSON in the form of a Python dict.
        
        If the CJSON does not specify the overall charge and spin, a neutral
        singlet is assumed, regardless of the chemical feasibility of that, unless the
        values are specified as arguments.
        """
        logger.debug("Instantiating a geometry from a cjson")
        atoms = []
        for i, atomic_no in enumerate(cjson_dict["atoms"]["elements"]["number"]):
            atoms.append(
                Atom(
                    get_element_symbol(atomic_no),
                    cjson_dict["atoms"]["coords"]["3d"][3*i],
                    cjson_dict["atoms"]["coords"]["3d"][3*i + 1],
                    cjson_dict["atoms"]["coords"]["3d"][3*i + 2],
                )
            )
        charge = charge if charge else cjson_dict.get("properties", {}).get("totalCharge", 0)
        spin = spin if spin else cjson_dict.get("properties", {}).get("totalSpinMultiplicity", 1) - 1
        return Geometry(atoms, charge, spin)

    @classmethod
    def from_file(
        cls,
        file: os.PathLike,
        format: str = None,
        multi: bool = False,
        charge: int = None,
        spin: int = None,
    ):
        """Create a `Geometry` object from an XYZ or CJSON file.
        
        The format can be specified by passing either ".xyz" or ".cjson" as the `format`
        argument, or it can be left to automatically be detected based on the filename
        ending.

        Charge and spin are handled as by the `from_xyz()` and `from_cjson()` methods:
        - if the file is a CJSON, charge and spin will be read from the file if present,
          then will default to 0;
        - if the file is an XYZ, they will be assumed to be 0.
        
        In all cases passing them as arguments will override everything.

        The method attempts to automatically detect an XYZ file containing multiple
        structures, parse as appropriate, and return a list of `Geometry` objects.
        If you know that a file contains multiple structures, or you wish to make sure
        that the return value is always a list, even for a single geometry, you can
        force this mode by passing `multi=True`.
        """
        logger.debug(f"Loading a geometry from {file}")
        filepath = Path(file)
        # Autodetect format of file
        if format is None:
            format = filepath.suffix

        if format == ".xyz":
            with open(filepath, encoding="utf-8") as f:
                xyz_lines = f.read().split("\n")
            charge = charge if charge else 0
            spin = spin if spin else 0
            # Detect multiple structures in single xyz file
            # Make the reasonable assumption that all structures have the same number of
            # atoms and that therefore the first line of the file repeats itself
            atom_count_line = xyz_lines[0]
            n_structures = xyz_lines.count(atom_count_line)
            if n_structures > 1 or multi:
                return cls.from_multi_xyz(xyz_lines, charge=charge, spin=spin)
            else:
                return cls.from_xyz(xyz_lines, charge=charge, spin=spin)

        if format == ".cjson":
            with open(filepath, encoding="utf-8") as f:
                cjson = json.load(f)
            return cls.from_cjson(cjson, charge=charge, spin=spin)
