import json
import os
from collections import namedtuple
from pathlib import Path

from .convert import get_atomic_number


Atom = namedtuple("Atom", ["element", "x", "y", "z"])


class Geometry:
    def __init__(
        self,
        atoms: list[Atom] = None,
        cjson: dict = None,
        xyz: list[str] = None,
        _comment: str | None = None,
    ):
        if atoms is not None:
            self.atoms = atoms
        elif cjson is not None:
            self.atoms = Geometry.from_cjson(cjson).atoms
        elif xyz is not None:
            self.atoms = Geometry.from_xyz(xyz).atoms
        self._comment = _comment
    
    def __iter__(self):
        """Geometries are iterable over their Atoms."""
        return iter(self.atoms)
    
    def to_xyz(self, comment: str | None = None) -> list[str]:
        if comment is None:
            comment = self._comment if self._comment else "xyz prepared by py-xtb"
        xyz = [str(len(self.atoms)), comment]
        for a in self.atoms:
            # Turn each atom (line of array) into a single string and add to xyz
            atom_line = "     ".join([
                a.element + (" " * (5 - len(a.element))),
                f"{a.x:.5f}",
                f"{a.y:.5f}",
                f"{a.z:.5f}",
            ])
            # Make everything line up by removing a space in front of each minus
            atom_line = atom_line.replace(" -", "-")
            xyz.append(atom_line)
        return xyz
    
    def to_cjson(self) -> dict:
        all_coords = []
        all_element_numbers = []
        for atom in self.atoms:
            element = atom[0]
            all_element_numbers.append(get_atomic_number(element))
            all_coords.extend([float(atom[1]), float(atom[2]), float(atom[3])])
        cjson = {
            "atoms": {
                "coords": {
                    "3d": all_coords,
                },
                "elements": all_element_numbers,
            },
        }
        return cjson

    def write_xyz(self, dest: os.PathLike) -> os.PathLike:
        # Make sure it ends with a newline
        lines = self.to_xyz() + [""]
        with open(dest, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    @classmethod
    def from_cjson(cls, cjson_dict: dict):
        return Geometry()

    @classmethod
    def from_xyz(cls, xyz_lines: list[str]):
        n_atoms = int(xyz_lines[0])
        atoms = []
        for atom_line in xyz_lines[2:]:
            atom_parts = atom_line.split()
            # Guard against empty final line or line starting with something other than
            # an element symbol
            if len(atom_parts) > 0 and atom_parts[0].isalpha():
                atoms.append(
                    Atom(atom_parts[0], *[float(n) for n in atom_parts[1:]])
                )
        return Geometry(atoms, _comment=xyz_lines[1])
    
    @classmethod
    def from_multi_xyz(cls, xyz_lines: list[str]):
        atom_count_line = xyz_lines[0]
        geometries = []
        current_xyz = []
        for i, l in enumerate(xyz_lines):
            current_xyz.append(l)
            if i == len(xyz_lines) - 1 or xyz_lines[i+1] == atom_count_line:
                geometries.append(cls.from_xyz(current_xyz))
                current_xyz = []
        return geometries

    @classmethod
    def from_file(cls, file, format=None, multi=False):
        filepath = Path(file)
        # Autodetect format of file
        if format is None:
            format = filepath.suffix

        if format == ".xyz":
            with open(filepath, encoding="utf-8") as f:
                xyz_lines = f.read().split("\n")
            # Detect multiple structures in single xyz file
            # Make the reasonable assumption that all structures have the same number of
            # atoms and that therefore the first line of the file repeats itself
            atom_count_line = xyz_lines[0]
            n_structures = xyz_lines.count(atom_count_line)
            if n_structures > 1 or multi:
                return cls.from_multi_xyz(xyz_lines)
            else:
                return cls.from_xyz(xyz_lines)

        if format == ".cjson":
            with open(filepath, encoding="utf-8") as f:
                cjson = json.load(f)
            return cls.from_cjson(cjson)
