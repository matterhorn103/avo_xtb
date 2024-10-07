# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of py-xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

from pathlib import Path

from .run import run_xtb


def optimize(
    geom_file: Path,
    charge: int = 0,
    multiplicity: int = 1,
    solvation: str | None = None,
    method: int = 2,
    level: str = "normal",
) -> tuple[Path, float]:
    """Return optimized geometry as file in same format as the input, along with the energy."""
    unpaired_e = multiplicity - 1
    command = [
        "xtb",
        geom_file,
        "--opt",
        level,
        "--chrg",
        str(charge),
        "--uhf",
        str(unpaired_e),
        "--gfn",
        str(method),
    ]

    # Add solvation if requested
    if solvation is not None:
        command.extend(["--alpb", solvation])
    # Run xtb from command line
    calc, out_file, energy = run_xtb(command, geom_file)
    # Return path to geometry file with same suffix, along with energy
    return geom_file.with_stem("xtbopt"), energy
