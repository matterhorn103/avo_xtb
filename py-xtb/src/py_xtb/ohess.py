# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of py-xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

from pathlib import Path

from .run import run_xtb


def opt_freq(
    geom_file: Path,
    charge: int = 0,
    multiplicity: int = 1,
    solvation: str | None = None,
    method: int = 2,
    level: str = "normal",
) -> tuple[Path, Path, float]:
    """Optimize geometry then calculate vibrational frequencies. Distort and reoptimize if negative frequency detected."""
    spin = multiplicity - 1
    command = [
        "xtb",
        geom_file,
        "--ohess",
        level,
        "--chrg",
        str(charge),
        "--uhf",
        str(spin),
        "--gfn",
        str(method),
    ]
    # Add solvation if requested
    if solvation is not None:
        command.extend(["--alpb", solvation])
    # Run xtb from command line
    calc, out_file, energy = run_xtb(command, geom_file)

    # Make sure the first calculation has finished
    # (How?)

    # Check for distorted geometry
    # (Generated automatically by xtb if result had negative frequency)
    # If so, rerun
    distorted_geom = geom_file.with_stem("xtbhess")
    if distorted_geom.exists():
        calc, out_file, energy = run_xtb(command, distorted_geom)

    # Return the path of the Gaussian file generated
    return geom_file.with_stem("xtbopt"), geom_file.with_name("g98.out"), energy
