# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of py-xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

from .geometry import Geometry
from .run import Calculation


def energy(
    input_geom: Geometry,
    charge: int = 0,
    multiplicity: int = 1,
    solvation: str | None = None,
    method: int = 2,
    return_calc: bool = False,
) -> float:
    """Calculate energy in hartree for given geometry."""

    unpaired_e = multiplicity - 1
    calc = Calculation(
        input_geometry=input_geom,
        options={
            "chrg": charge,
            "uhf": unpaired_e,
            "gfn": method,
            "alpb": solvation,
        }
    )
    calc.run()
    if return_calc:
        return calc.energy, calc
    else:
        return calc.energy
