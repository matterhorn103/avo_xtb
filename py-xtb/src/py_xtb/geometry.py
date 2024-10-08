import json
import os
from collections import namedtuple
from pathlib import Path


Atom = namedtuple("Atom", ["element", "x", "y", "z"])


class Geometry:
    def __init__(
        self,
        atoms: list[Atom] = None,
        cjson: dict = None,
        xyz: list[str] = None,
    ):
        if atoms is not None:
            self.atoms = atoms
        elif cjson is not None:
            self.atoms = Geometry.from_cjson(cjson).atoms
        elif xyz is not None:
            self.atoms = Geometry.from_xyz(xyz).atoms
    
    def to_xyz(self) -> list[str]:
        xyz = [str(len(self.atoms)), "xyz prepared by py-xtb"]
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
            if len(atom_parts) > 0:
                atoms.append(
                    Atom(atom_parts[0], *[float(n) for n in atom_parts[1:]])
                )
        return Geometry(atoms)

    @classmethod
    def from_file(cls, file, format=None):
        filepath = Path(file)
        # Autodetect format of file
        if format is None:
            format = filepath.suffix
        if format == ".xyz":
            with open(filepath, encoding="utf-8") as f:
                file_lines = f.read().split("\n")
            return cls.from_xyz(file_lines)
        if format == ".cjson":
            with open(filepath, encoding="utf-8") as f:
                cjson = json.load(f)
            return cls.from_cjson(cjson)
