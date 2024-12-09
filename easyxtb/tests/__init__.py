# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

from easyxtb import Geometry, Atom

def round_atom_coordinates(atoms: list[Atom], precision: int = 12) -> list[Atom]:
    # Often have to account for difference in precision between formats or sources
    rounded_atoms = []
    for atom in atoms:
        rounded_atoms.append(
            Atom(
                atom.element,
                round(atom.x, precision),
                round(atom.y, precision),
                round(atom.z, precision),
            )
        )
    return rounded_atoms

def equal_geom(geom1: Geometry, geom2: Geometry, precision: float = 7e-5) -> bool:
    for i in range(len(geom1.atoms)):
        diffs = [
            abs(geom1.atoms[i].x - geom2.atoms[i].x),
            abs(geom1.atoms[i].y - geom2.atoms[i].y),
            abs(geom1.atoms[i].z - geom2.atoms[i].z),
        ]
        if (
            geom1.atoms[i].element != geom2.atoms[i].element
            or not all([diff <= precision for diff in diffs])
        ):
            print(geom1.atoms[i])
            print(geom2.atoms[i])
            print()
            return False
    return True

def equal_freqs(freqs1: list, freqs2: list, precision: float = 1.0) -> bool:
    for i, f in enumerate(freqs1):
        diff = abs(f["frequency"] - freqs2[i]["frequency"])
        if not diff <= precision:
            print(f)
            print(freqs2[i])
            print()
            return False
    return True
