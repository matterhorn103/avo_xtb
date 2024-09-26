import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Atom:
    element: str
    x: float
    y: float
    z: float


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
            atom_line = "     ".join([a.element, str(a.x), str(a.y), str(a.z)])
            # Make everything line up by removing a space in front of each minus
            atom_line.replace(" -", "-")
            xyz.append(atom_line)
        return xyz

    def write_xyz(self, dest: os.PathLike, final_newline=True) -> os.PathLike:
        xyz = self.to_xyz()
        if final_newline:
            xyz.append("")
        with open(dest, "w", encoding="utf-8") as f:
            f.write("\n".join(xyz))

    @classmethod
    def from_cjson(cls, cjson_dict: dict):
        return Geometry()

    @classmethod
    def from_xyz(cls, xyz_lines: list[str]):
        atoms = []
        for line in xyz_lines[2:]:
            parts = line.split()
            if len(parts) < 4:
                # Reached end of geometry
                break
            new_atom = Atom(parts[0], float(parts[1]), float(parts[2]), float(parts[3]))
            atoms.append(new_atom)
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
        

if __name__ == "__main__":
    f = Path.home() / "calcs/input.xyz"
    geom = Geometry.from_file(f)

    print(geom)
    print(geom.atoms)
    print(geom.to_xyz())
