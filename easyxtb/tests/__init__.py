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

def equal_geom(geom1: Geometry, geom2: Geometry, precision: int = 12) -> bool:
    rounded1 = round_atom_coordinates(geom1.atoms, precision)
    rounded2 = round_atom_coordinates(geom2.atoms, precision)
    for i in range(len(rounded1)):
        if rounded1[i] != rounded2[i]:
            print(rounded1[i])
            print(rounded2[i])
            print()
    return rounded1 == rounded2
